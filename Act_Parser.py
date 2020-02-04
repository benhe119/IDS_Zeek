# Library imports
import lxml.etree
import numpy as np
import re
import itertools
import collections.abc

# Get directory for all the XMLs files
path = './XMLs'
# Notes on XML parsing
# <name x="5" y="5">busbar_IED</name>
# name is tag, x="5" y="5" is attrib, busbar_IED is text. P

#xml_file = ET.parse(path+"/Test_Busbar.xml")
xml_file = lxml.etree.parse(path+"/Test_Busbar-Carmen-HC-latest.xml")
root_xml = xml_file.getroot()

# Function to get names of templates
def get_names(xml):
    names = []
    for elem in xml.findall(".//template/name"):
        names.append(elem.text)
        #print(elem.text)
    return names


class xml_data():
    def __init__(self, name):
        self.name = name
        self.node = root_xml.find(".//template[name='{}']".format(self.name))

    def get_attribute_names(self, element):
        if element is None:
            # If there is no element in the elements variable
            return "Error: E1"
        try:
            attrib_list = [el.attrib.get('kind') for el in element.findall('.//label')]
            return attrib_list
        except:
            # If there is no "kind" in the element
            return "Error: E2"

    def get_element_value(self, element, attrib_name):
        try:
            value = (element.find(".//*[@kind='{}']".format(attrib_name))).text
            return value.replace("\n", "")
        except:
            # There is no attribute name in "kind" for the given element
            return "Error: E3"

    def form_dictionary(self, elements):
        self.xml_values = []
        for e in elements:
            dict_xml = {}
            dict_xml["vector"] = [e]
            attrib_list = self.get_attribute_names(e)
            for attrib in attrib_list:
                dict_xml[attrib] = []
            self.xml_values.append(dict_xml)
        print("end")

    def find_next_hop_element(self, hops=1):
        for cnt in range(len(self.xml_values)):
            element = self.xml_values[cnt]["vector"]
            next_element = self.find_target(element[0])
            if next_element != 0:
                element.append(next_element)
            self.xml_values[cnt]["vector"] = element

    #Find target from the given element's source
    def find_target(self, element):
        src = (element.find(".//source")).attrib["ref"]
        finder = (self.node.findall(".//target[@ref='{}']/..".format(src)))
        if len(finder) == 1:
            return finder[0]
            # print(self.vector)
        else:
            print("No targets found from source! Returning the vectors")
            return 0

    def store_values(self, elements):
        self.form_dictionary(elements)
        self.find_next_hop_element()
        for cnt in range(len(self.xml_values)):
            vector_elems = self.xml_values[cnt]["vector"]
            for elem in vector_elems:
                for key in self.xml_values[cnt]:
                    if key != "vector":
                        elem_text = self.get_element_value(elem, key)
                        ## Add synchronization element to guard in the second hop
                        if "?" in elem_text and vector_elems.index(elem) == 1:
                            self.xml_values[cnt]["guard"].append(elem_text)
                        else:
                            self.xml_values[cnt][key].append(elem_text)

    # Function to locate the initial point "!"
    def find_condition(self):
        # "!" is used as precondition check
        cond_loc = self.node.xpath(".//*[contains(text(), '!')][not(contains(text(), '!='))]/..")
        self.no_of_cond = len(cond_loc)
        return cond_loc

xml_names = get_names(root_xml)
xml_dict = {}
for name in xml_names:
    xml_dict[name]=xml_data(name)
    cond_check = xml_dict[name].find_condition()
    xml_dict[name].store_values(cond_check)
    print("Checkpoint")

class process_conditions():
    def __init__(self, name, matrix):
        self.name = name
        self.xml_dict = matrix
        self.attack_params_dict = {}

    def flatten(self, l):
        for el in l:
            if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
                yield from self.flatten(el)
            else:
                yield el

    def remove_space(self, string):
        pattern = re.compile(r'\s+')
        return re.sub(pattern, '', string)

    def get_global_variables(self):
        raw_global_vars = root_xml.xpath("/nta/declaration/text()")[0]
        raw_global_vars = raw_global_vars.replace("\n", "")
        raw_global_vars = raw_global_vars.split(";")
        variable_types = ["int", "bool"]
        raw_global_vars = [var for var in raw_global_vars for type in variable_types if type in var]
        self.global_vars_dict = {}
        for type in variable_types:
            temp_list = [var.strip(type) for var in raw_global_vars if type in var]
            temp_list = [self.remove_space(var) for var in temp_list]
            temp_dict = {}
            for temp in temp_list:
                temp = temp.split("=")
                temp_dict["glo_"+temp[0]] = temp[1]
            self.global_vars_dict[type] = temp_dict
        print("end")

    def to_global_vars(self):
        print(1)

    def get_variables_from_operator(self, string_list):
        return_list = []
        for str in string_list:
            re.split('<(?!=)|<=|==|=(?!=)|>(?!=)|>=', str)
        print(1)

    def get_guard(self):
        guard_list = []
        for condition in self.xml_dict:
            #remove error codes
            temp_list = [con for con in condition["guard"] if "Error" not in con]
            temp_list = [re.split("&&", con) for con in temp_list] #Split variables with &&
            temp_list = self.flatten(temp_list)
            #Remove special characters
            #temp_list = [re.sub('[!@#$?]', '', con) for con in temp_list]
            guard_list.append(list(temp_list))
        return guard_list

    def is_bool(self, b):
        b_list = ["True", "TRUE", "true", "False", "FALSE", "false"]
        try:
            if b in b_list:
                return True
        except:
            return False

    def is_numeric(self, b):
        if b.isnumeric():
            return True
        else:
            return False

    def is_counter(self, string):
        container = ["++", "+1", "+ 1"]
        try:
            for c in container:
                if c in string:
                    return True
        except:
            return False

    def make_global_guard(self, guard_list):
        operator_split = '<(?!=)|<=|==|=(?!=)|>(?!=)|>='
        replace_dict = {}
        #for guard in guard_list:
        #    for operator in guard:
        for c1 in range(len(guard_list)):
            for c2 in range(len(guard_list[c1])):
                operator = guard_list[c1][c2]
                var_temp = re.sub(" ","", operator)
                var_temp = re.split(operator_split, var_temp)
                if len(var_temp) == 2 and "glo_" not in var_temp[0]:
                    if self.is_numeric(var_temp[1]) or self.is_counter(var_temp[1]) or self.is_bool(var_temp[1]):
                        guard_list[c1][c2] = guard_list[c1][c2].replace(var_temp[0], "glo_"+var_temp[0])
                    else:
                        guard_list[c1][c2] = guard_list[c1][c2].replace(var_temp[0], "glo_" + var_temp[0])
                        guard_list[c1][c2] = guard_list[c1][c2].replace(var_temp[1], "glo_" + var_temp[1])
                if len(var_temp) == 1 and "glo_" not in var_temp[0]:
                    guard_list[c1][c2] = guard_list[c1][c2].replace(var_temp[0], "glo_"+var_temp[0])
        return guard_list

    def get_parameters(self, attack_type):
        #Making a guard dictionary and adding to main attack_params_dict
        guard_list = self.get_guard()
        guard_list = self.make_global_guard(guard_list)
        cond_dict = {}
        for c in range(len(guard_list)):
            guard_dict = {}
            cond_dict["cond_" + str(c)] = guard_dict
            cond_dict["cond_"+str(c)]["guard"] = guard_list[c]
            self.attack_params_dict[attack_type] = cond_dict

        #Sub-conditions


# Only for busbar_IED1
processed_variables_dict = {}
xml_dict_list = xml_dict["busbar_IED1"].xml_values
processed_variables_dict["busbar_IED1"] = process_conditions("busbar_IED1", xml_dict_list)
guard_list = processed_variables_dict["busbar_IED1"].get_parameters(attack_type="Injection")
processed_variables_dict["busbar_IED1"].get_global_variables()
processed_variables_dict["busbar_IED1"].make_negations(guard_list)


class create_variables():
    def __init__(self, name, matrix_list, no_of_cond, negated_guard_dict):
        self.name = name
        self.dict_matrix = matrix_list
        self.no_of_cond = no_of_cond
        self.negated_guard_dict = negated_guard_dict

    def flatten(self, l):
        for el in l:
            if isinstance(el, collections.abc.Iterable) and not isinstance(el, (str, bytes)):
                yield from self.flatten(el)
            else:
                yield el

    def get_raw_list(self):
        all_values = list(self.dict_matrix.values())
        merged_list = list(self.flatten(all_values))
        # drop duplicates
        final_list = list(dict.fromkeys(merged_list))
        return final_list

    def is_bool(self, b):
        b_list = ["True", "TRUE", "true", "False", "FALSE", "false"]
        try:
            if b in b_list:
                return True
        except:
            return False

    def is_numeric(self, b):
        if b.isnumeric():
            return True
        else:
            return False

    def is_counter(self, string):
        container = ["++", "+1", "+ 1"]
        try:
            for c in container:
                if c in string:
                    return True
        except:
            return False

    def get_global_variables(self):
        temp_var_list = []
        for var in self.final_local_variables:
            temp_var_list.append("glo_"+var)
        self.final_global_variables = temp_var_list.copy()

    def get_local_variables(self):
        final_var_list = []
        function_init = []
        final_list = self.get_raw_list()
        #split_final_list = self.string_split(final_list)
        for st in final_list:
            var_temp = st.strip()
            var_temp = var_temp.replace(" ", "")
            var_temp = re.split('<(?!=)|<=|==|=(?!=)|>(?!=)|>=', var_temp)
            if len(var_temp) == 2:
                #Check if the string after operator symbol is numeric or boolean
                if self.is_bool(var_temp[1]):
                    final_var_list.append(var_temp[0])
                    function_init.append(var_temp[0]+": bool")
                elif self.is_numeric(var_temp[1]):
                    final_var_list.append(var_temp[0])
                    function_init.append(var_temp[0]+": double")
                elif self.is_counter(var_temp[1]):
                    final_var_list.append(var_temp[0])
                    function_init.append(var_temp[0]+": count")
                else:
                    final_var_list.append(var_temp[0])
                    function_init.append(var_temp[0]+": double")
                    final_var_list.append(var_temp[1])
                    function_init.append(var_temp[1]+": double")
            if len(var_temp) == 1:
                if self.is_counter(var_temp[0]):
                    final_var_list.append(var_temp[0].strip("++"))
                    function_init.append((var_temp[0].strip("++"))+": count")

        self.final_local_variables = final_var_list
        self.function_init = ", ".join(function_init)

## The for loop in dictionary is to be created. For time being only one variable is being used.
global_var_dict = {}
v1 = "busbar_IED"
v2 = negation_dict[v1].dict_matrix
v3 = negation_dict[v1].no_of_cond
v4 = negation_dict[v1].negated_guard_dict
global_var_dict[v1] = create_variables(v1, v2, v3, v4)
global_var_dict[v1].get_local_variables()
global_var_dict[v1].get_global_variables()

print("end")

class injection_attack_variables():
    def __init__(self, name, matrix_list, no_of_cond, negated_guard_dict, final_global_variables,func_init):
        self.name = name
        self.dict_matrix = matrix_list
        self.no_of_cond = no_of_cond
        self.negated_guard_dict = negated_guard_dict
        self.final_global_variables = final_global_variables
        self.function_init = func_init


class create_functions_bro():
    def __init__(self, name, matrix_list, no_of_cond, negated_guard_dict, final_global_variables, func_init):
        self.name = name
        self.dict_matrix = matrix_list
        self.no_of_cond = no_of_cond
        self.negated_guard_dict = negated_guard_dict
        self.final_global_variables = final_global_variables
        self.function_init = func_init
        self.create_injection_function((2,17))

    def injection_preconditions(self, injection_dict, cond_template_dict):
        # Pre_cond_1
        for c in range(self.no_of_cond):
            cond_template_dict[c]["pre_cond_1"] = "("+self.negated_guard_dict["Injection"][c]+")"
        # Pre_cond_2; check if left is in right
        for c in range(self.no_of_cond):
            dict_assignment = self.dict_matrix["assignment"][c]
            for d in dict_assignment:
                var_temp = d.strip()
                var_temp = var_temp.replace(" ", "")
                var_temp = re.split('<(?!=)|<=|==|=(?!=)|>(?!=)|>=', var_temp)
                if len(var_temp) > 1:
                    if var_temp[0] in var_temp[1]:
                        cond_template_dict[c]["pre_cond_2"] = "({} == glo_{}+1)".format(var_temp[0], var_temp[0])
                        cond_template_dict[c]["pre_cond_3"] = "glo_{} = {};".format(var_temp[0], var_temp[0])

        return cond_template_dict
        print("end")


    def create_injection_function(self, line):
        import_template = open("Injection_template.txt", "r")
        inj_template = import_template.readlines()
        cond_template = []
        # Extracting from template for the conditions to repeat
        for num in range(line[0], line[1]):
            cond_template.append(inj_template[num])
        cond_template = "".join(cond_template)
        injection_dict = {
            "func_init": self.function_init,
            "pre_cond_1":"",
            "pre_cond_2": "",
            "pre_cond_3": "",
            "next_pre_cond":""
        }
        cond_template_dict = [injection_dict]*self.no_of_cond
        con_dict = self.injection_preconditions(injection_dict, cond_template_dict)
        make_function = []
        # Function title
        for n1 in range(0, line[0]):
            make_function.append(inj_template[n1]%con_dict[0])
        for n2 in range(self.no_of_cond):
            print(cond_template%con_dict[n2])
            make_function.append(cond_template%con_dict[n2])
        for n3 in range(line[1], len(inj_template)):
            make_function.append(inj_template[n3])
        print("".join(make_function))
        print("end")

functions_bro_dict = {}
v1 = "busbar_IED"
v2 = global_var_dict[v1].dict_matrix
v3 = global_var_dict[v1].no_of_cond
v4 = global_var_dict[v1].negated_guard_dict
v5 = global_var_dict[v1].final_global_variables
v6 = global_var_dict[v1].function_init
functions_bro_dict[v1] = create_functions_bro(v1, v2, v3, v4, v5, v6)
print("end")


'''
#print(xml_dict['busbar_IED'].matrix[0])
#print(xml_dict['feeder_IED'].matrix[0])
print("end")
#Step 1: Form class using xml_data("Used names"). Maxtrix is formed using ids in one of template name
#Step 2: Find guard condition which has "!" which will return matrix with vectors. Currently, it is expected to have
#only one guard condition with "!"
'''