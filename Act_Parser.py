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
        self.function_init = {}

    def flatten(self, l):
        for el in l:
            if isinstance(el, collections.abc.Iterable) and not isinstance(el, (str, bytes)):
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
        variable_types = ["int", "bool", "clock"]
        raw_global_vars = [var for var in raw_global_vars for type in variable_types if type in var]
        self.global_vars_dict = {}
        for type in variable_types:
            temp_list = [var.strip(type) for var in raw_global_vars if type in var]
            temp_list = [self.remove_space(var) for var in temp_list]
            temp_dict = {}
            for temp in temp_list:
                temp = temp.split("=")
                if len(temp)==2:
                    temp_dict["glo_"+temp[0]] = temp[1]
                if len(temp)==1:
                    temp_dict["glo_" + temp[0]] = ""
            self.global_vars_dict[type] = temp_dict
        print("end")


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
            temp_list = [re.split(",", con) for con in temp_list]  # Split variables with ,
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

    def is_arithmetic(self, string_1, string_2):
        if string_1 in string_2:
            return True
        else:
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
                    if self.is_numeric(var_temp[1]) or self.is_bool(var_temp[1]):
                        guard_list[c1][c2] = guard_list[c1][c2].replace(var_temp[0], "glo_"+var_temp[0])
                    else:
                        guard_list[c1][c2] = guard_list[c1][c2].replace(var_temp[0], "glo_" + var_temp[0])
                        guard_list[c1][c2] = guard_list[c1][c2].replace(var_temp[1], "glo_" + var_temp[1])
                if len(var_temp) == 1 and "glo_" not in var_temp[0]:
                    guard_list[c1][c2] = guard_list[c1][c2].replace(var_temp[0], "glo_"+var_temp[0])
        return guard_list

    def get_assignment(self):
        assignment_list = []
        for condition in self.xml_dict:
            #remove error codes
            temp_list = [con for con in condition["assignment"] if "Error" not in con]
            temp_list = [re.split("&&", con) for con in temp_list] #Split variables with &&
            temp_list = self.flatten(temp_list)
            temp_list = [re.split(",", con) for con in temp_list]  # Split variables with ,
            temp_list = self.flatten(temp_list)
            #Remove special characters
            #temp_list = [re.sub('[!@#$?]', '', con) for con in temp_list]
            assignment_list.append(list(temp_list))
        return assignment_list

    def make_assignment_rules(self, assignment_list):
        operator_split = '<(?!=)|<=|==|=(?!=)|>(?!=)|>='
        #for guard in guard_list:
        #    for operator in guard:
        for c1 in range(len(assignment_list)):
            for c2 in range(len(assignment_list[c1])):
                operator = assignment_list[c1][c2]
                var_temp = re.sub(" ","", operator)
                var_temp_1 = var_temp[:]
                var_temp = re.split(operator_split, var_temp)
                flag_1 = False
                if len(var_temp) == 2:
                    #Condition I if expression is a boolean operation, use local variable and
                    # check that the condition is true
                    if self.is_numeric(var_temp[1]):
                        assignment_list[c1][c2] = var_temp[0] + " == " + var_temp[1]
                        flag_1 = True
                    # Condition III: if expression is an assignment operation. use local variable
                    # declaration and perform equality check
                    elif self.is_bool(var_temp[1]) and flag_1 != True:
                        assignment_list[c1][c2] = var_temp[0] + " == " + var_temp[1]
                        flag_1 = True
                    #Condition II: if expression is an arithmetic operation, verify the condition
                    # is correct by equating the local variable to the global variable
                    elif self.is_counter(var_temp_1) and flag_1 != True:
                        assignment_list[c1][c2] = var_temp[0] + " == glo_" + var_temp[0] + "+1"
                        flag_1 = True
                    #else:
                    #    assignment_list[c1][c2] = assignment_list[c1][c2].replace(var_temp[0], "glo_"+var_temp[0])
                    #    assignment_list[c1][c2] = assignment_list[c1][c2].replace(var_temp[1], "glo_" + var_temp[1])
                if len(var_temp) == 1:
                    if self.is_counter(var_temp[0]):
                        var_temp = re.sub('[++,+1,+ 1]', '', var_temp[0])
                        assignment_list[c1][c2] = var_temp + " == glo_" + var_temp + " +1"
        return assignment_list

    def get_update_variables(self, attack_type):
        for cond in range(len(self.attack_params_dict[attack_type])):
            temp_list = []
            for key in self.attack_params_dict[attack_type][cond]:
                if key == "assignment":
                    for v in self.attack_params_dict[attack_type][cond][key]:
                        var_temp = v.replace(" ", "")
                        var_temp = re.split('==', var_temp)
                        # Rule #1
                        if self.is_bool(var_temp[1]):
                            if var_temp[1] in "True true":
                                temp_list.append("glo_"+var_temp[0]+" = False;")
                            else:
                                temp_list.append("glo_" + var_temp[0] + " = True;")
                        # Rule #2
                        if self.is_numeric(var_temp[1]):
                            temp_list.append("glo_"+var_temp[0] + " = "+var_temp[0]+";")
                        # Rule #3
                        if self.is_counter(v):
                            temp_list.append("glo_"+var_temp[0] + " = "+var_temp[0]+";")
            self.attack_params_dict[attack_type][cond]["update"] = temp_list


    def get_parameters(self, attack_type):
        #Making a guard dictionary and adding to main attack_params_dict
        guard_list = self.get_guard()
        guard_list = self.make_global_guard(guard_list)
        cond_list = []
        for c in range(len(guard_list)):
            guard_dict = {}
            cond_list.append(guard_dict)
            cond_list[(c)]["guard"] = guard_list[c]
        self.attack_params_dict[attack_type] = cond_list
        assignment_list = self.get_assignment()
        assignment_list = self.make_assignment_rules(assignment_list)
        #Sub-conditions
        for c in range(len(assignment_list)):
            assignment_dict = {}
            cond_list[(c)]["assignment"] = assignment_list[c]
        self.attack_params_dict[attack_type] = cond_list
        update_list = self.get_update_variables(attack_type)

    def get_function_init(self, attack_type):
        final_var_list = []
        function_init = []
        final_list = []
        for cond in self.attack_params_dict[attack_type]:
            for key in cond:
                if key == "assignment":
                    final_list.extend(cond[key])
        final_list = list(dict.fromkeys(final_list))
        # split_final_list = self.string_split(final_list)
        for st in final_list:
            var_temp = st.strip()
            var_temp = var_temp.replace(" ", "")
            var_temp = re.split('<(?!=)|<=|==|=(?!=)|>(?!=)|>=', var_temp)
            if len(var_temp) == 2:
                # Check if the string after operator symbol is numeric or boolean
                if self.is_bool(var_temp[1]):
                    final_var_list.append(var_temp[0])
                    function_init.append(var_temp[0] + ": bool")
                elif self.is_numeric(var_temp[1]):
                    final_var_list.append(var_temp[0])
                    function_init.append(var_temp[0] + ": double")
                elif self.is_counter(var_temp[1]):
                    final_var_list.append(var_temp[0])
                    function_init.append(var_temp[0] + ": count")
                else:
                    final_var_list.append(var_temp[0])
                    function_init.append(var_temp[0] + ": double")
                    final_var_list.append(var_temp[1])
                    function_init.append(var_temp[1] + ": double")
            if len(var_temp) == 1:
                if self.is_counter(var_temp[0]):
                    final_var_list.append(var_temp[0].strip("++"))
                    function_init.append((var_temp[0].strip("++")) + ": count")

        #self.final_local_variables = final_var_list
        self.function_init[attack_type] = ", ".join(function_init)

# Only for busbar_IED1
processed_variables_dict = {}
xml_dict_list = xml_dict["busbar_IED1"].xml_values
processed_variables_dict["busbar_IED1"] = process_conditions("busbar_IED1", xml_dict_list)
processed_variables_dict["busbar_IED1"].get_global_variables()
processed_variables_dict["busbar_IED1"].get_parameters(attack_type="Inject & Flood")
processed_variables_dict["busbar_IED1"].get_function_init(attack_type = "Inject & Flood")


class create_function_bro():
    def __init__(self, name, params_list, function_init, global_vars_dict):
        self.name = name
        self.params_list = params_list
        self.function_init = function_init
        self.global_vars_dict= global_vars_dict
        #IF - Inject & Flood
        self.mapping_IF = {"pre_cond_1":"guard",
                           "pre_cond_2":"assignment",
                           "pre_cond_3": "update"}
        #Test
        self.create_inject_flood_function((2,17))

    def global_variables(self):
        global_vars = []
        for key in self.global_vars_dict:
            for var in self.global_vars_dict[key]:
                if self.global_vars_dict[key][var] == "":
                    global_vars.append("global " + var + ";")
                else:
                    global_vars.append("global " + var + " = " + self.global_vars_dict[key][var] + ";")
        return "\n".join(global_vars)

    def insert_precondition_IF(self, templater, parameters):
        template = templater[:]
        for n1 in range(len(template)):
            for key in template[n1]:
                try:
                    print(template[n1][key])
                    print(parameters[n1][self.mapping_IF[key]])
                    template[n1][key] =  1#" && ".join(parameters[c1][self.mapping_IF[key]])
                except:
                    continue

    def create_inject_flood_function(self, line, attack_type="Inject & Flood"):
        import_template = open("Injection_template.txt", "r")
        inj_template = import_template.readlines()
        cond_template = []
        # Extracting from template for the conditions to repeat
        for num in range(line[0], line[1]):
            cond_template.append(inj_template[num])
        cond_template = "".join(cond_template)
        injection_dict = {
            "func_init": self.function_init[attack_type],
            "pre_cond_1":"",
            "pre_cond_2": "",
            "pre_cond_3": "",
        }
        no_of_cond = len(self.params_list[attack_type])
        parameters = self.params_list[attack_type]
        con_dict = []
        for c in range(no_of_cond):
            cond_template_dict = injection_dict.copy()
            for key in cond_template_dict:
                try:
                    if key == "pre_cond_3":
                        cond_template_dict[key] = " ".join(parameters[c][self.mapping_IF[key]])
                    else:
                        cond_template_dict[key] =  " && ".join(parameters[c][self.mapping_IF[key]])

                except:
                    continue
            con_dict.append(cond_template_dict)

        make_function = []
        # Function title
        for n1 in range(0, line[0]):
            make_function.append(inj_template[n1]%con_dict[0])
        for n2 in range(no_of_cond):
            print(cond_template%con_dict[n2])
            make_function.append(cond_template%con_dict[n2])
        for n3 in range(line[1], len(inj_template)):
            make_function.append(inj_template[n3])

        global_variables = self.global_variables()
        function_IJ = "".join(make_function)
        f = open("IJ_Function.txt", "w+")
        f.write(global_variables)
        f.write("\n\n")
        f.write(function_IJ)
        f.close()

functions_bro_dict = {}
v1 = "busbar_IED1"
v2 = processed_variables_dict[v1].attack_params_dict
v3 = processed_variables_dict[v1].function_init
v4 = processed_variables_dict[v1].global_vars_dict
functions_bro_dict[v1] = create_function_bro(v1, v2, v3, v4)



'''
#print(xml_dict['busbar_IED'].matrix[0])
#print(xml_dict['feeder_IED'].matrix[0])
print("end")
#Step 1: Form class using xml_data("Used names"). Maxtrix is formed using ids in one of template name
#Step 2: Find guard condition which has "!" which will return matrix with vectors. Currently, it is expected to have
#only one guard condition with "!"
'''