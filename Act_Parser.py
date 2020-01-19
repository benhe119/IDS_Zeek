# Library imports
import lxml.etree
import numpy as np
import re
import itertools

# Get directory for all the XMLs files
path = './XMLs'
# Notes on XML parsing
# <name x="5" y="5">busbar_IED</name>
# name is tag, x="5" y="5" is attrib, busbar_IED is text. P

#xml_file = ET.parse(path+"/Test_Busbar.xml")
xml_file = lxml.etree.parse(path+"/Test_Busbar.xml")
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
        self.id_names = self.get_ids()
        self.matrix = self.form_matrix()
        self.vector = []

    # Getting id of the template name
    def get_ids(self):
        find_src = self.node.findall(".//source")
        find_tgt = self.node.findall(".//target")
        ids = [at.attrib["ref"] for at in find_src]
        ids.extend([at.attrib["ref"] for at in find_src])
        id_names = sorted(set(ids))
        return id_names

    # Function to locate the initial point "!"
    def find_condition(self):
        # "!" is used as precondition check
        cond_loc = self.node.xpath(".//*[contains(text(), '!')][not(contains(text(), '!='))]/..")
        self.no_of_cond = len(cond_loc)
        #Need another way to find !, find guard and find !
        return cond_loc

    def find_vectors(self, element, hop=1): # Element is the starting point where '!' is found
        for elem in element:
            self.vector = []
            src = (elem.find(".//source")).attrib["ref"]
            tgt = (elem.find(".//target")).attrib["ref"]
            self.vector.append(elem) #Append the initial condition
            target_elem = elem
            for h in range(hop):
                target_elem = self.find_target(target_elem)
                if target_elem == 0:
                    break
                else:
                    self.vector.append(target_elem)
            self.store_data(self.vector)
        del self.idx, self.vector, self.dim #deleting variables to have a clean dictionary with matrix
        return self.matrix

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

    # Form a null matrix based on the ID names from template. For example id0, id1, id2 represents a 3x3 matrix
    # Also create a 3rd dimension with values obtained from "kind" in the xml e.g."guard" has 3x3 matrix for a template
    def form_matrix(self):
        self.idx = {}
        temp_cnt = 0
        for id in self.id_names:
            self.idx[id] = temp_cnt
            temp_cnt = temp_cnt + 1
        dim_names = set([elem.attrib["kind"] for elem in self.node.findall(".//*[@kind]")])
        self.dim = {}
        temp_cnt = 0
        for d in dim_names:
            self.dim[d] = temp_cnt
            temp_cnt = temp_cnt + 1
        m_matrix = {}
        for d in self.dim:
            m_matrix[d] = np.zeros((len(self.idx), len(self.idx)), dtype=object) # no. of Dimension, row, colmuns
        return m_matrix

    def store_data(self, elements):
        for elem in elements:
            row = (elem.find(".//source")).attrib["ref"]
            col = (elem.find(".//target")).attrib["ref"]
            kind = [e.attrib["kind"] for e in elem.findall(".//*[@kind]")]

            for label in kind:
                mtx = self.matrix[label].item((self.idx[row], self.idx[col]))
                elem_txt = (elem.find(".//*[@kind='{}']".format(label))).text
                if mtx is 0 or mtx is None:
                    self.matrix[label][self.idx[row], self.idx[col]] = [elem_txt]
                else:
                    if mtx is not None:
                        mtx.append(elem_txt)

    #Useless function at the moment!
    def src_tgt_list(self, elements):
        temp_list = []
        for elem in elements:
            src = elem.find(".//source").attrib["ref"]
            tgt = elem.find(".//target").attrib["ref"]
            temp_list.append((src,tgt))
        return temp_list

xml_names = get_names(root_xml)
xml_dict = {}
for name in xml_names:
    xml_dict[name]=xml_data(name)
    cond_check = xml_dict[name].find_condition()
    xml_dict[name].find_vectors(cond_check, hop=1)
    print("Checkpoint")
final_xmldata = xml_dict.copy()

class form_negations():
    def __init__(self, name, matrix, no_of_cond):
        self.name = name
        self.dict_matrix = matrix
        self.no_of_cond = no_of_cond
        self.attacks = ["Replay", "Flood", "Injection", "Delete"]
        self.attack_map = {
            "Replay": " || ",
            "Flood": " && ",
            "Injection": " || ",
            "Delete": " && "
        }
        self.negate_cond = {
            "Replay": True,
            "Flood": False,
            "Injection": True,
            "Delete": False
        }

    def add_space(self, string_list):
        temp_string = "+|+".join(string_list)
        temp_string = temp_string.strip()
        temp_string = temp_string.replace(" ", "")
        spaces = {"&&":" && ", "\|\|": " || ", "==": " == ", "!=": " != ",
                  ">=": " >= ", "<=": " <= ", ">(?!=)" : " > ", "<(?!=)": " < "}
        for s in spaces:
            temp_string = re.sub(s, " " + spaces[s] + " ", temp_string)
        return temp_string.split("+|+")

    def flatten_matrix(self):
        for key in self.dict_matrix:
            x1 = self.dict_matrix[key]
            x1 = x1[np.nonzero(x1)]
            self.dict_matrix[key] = x1
    # This function gets the guard. Currently, the guard is a matrix; this function will collapse matrix
    # to a list. The list if futher re-arranged based on the condition. For example if there are two conditions
    # in a template name, a list with in a list is created where list[0] will correspond to first condition guard.
    def get_guard(self):
        #guard_list = self.dict_matrix["guard"]
        #guard_list = guard_list[np.nonzero(guard_list)]
        self.flatten_matrix()
        guard_list = self.dict_matrix["guard"]
        for arr in guard_list:
            print("Number of guards = " + str(len(arr)))
            print("Num of conditions = " + str(self.no_of_cond))
            if len(arr) == self.no_of_cond:
                print(self.name)
                print("Conditions satisfied! Continuing to next step")
            else:
                print(self.name)
                print("Conditions not satisfied! Number of conditions and Number of guard must be equal")
                exit()
        temp_list = []
        for c in range(self.no_of_cond):
            x1 = [g[c] for g in guard_list]
            x1 = self.add_space(x1)
            temp_list.append(x1)
        guard_list = temp_list.copy()
        return guard_list

    def make_negations(self, guard_list):
        self.negated_guard_dict = {}
        for atk in self.attacks:
            temp_guard_list = []
            if self.negate_cond[atk] == True: # Negate if true
                for g in guard_list:
                    x1 = (["!("+s+")" for s in g])
                    x1 = (" "+self.attack_map[atk]+" ").join(x1)
                    temp_guard_list.append(x1)

            else:
                for g in guard_list:
                    x1 = (["(" + s + ")" for s in g])
                    x1 = (" "+self.attack_map[atk]+" ").join(x1)
                    temp_guard_list.append(x1)

            self.negated_guard_dict[atk] = temp_guard_list
        del self.attack_map, self.negate_cond
        return self.negated_guard_dict

# For final xml which is correct.
'''
negation_dict = {}
for key in final_xmldata:
    matrix = final_xmldata[key].matrix
    no_of_cond = final_xmldata[key].no_of_cond
    negation_dict[key] = form_negations(key, matrix, no_of_cond)
    guard_list = negation_dict[key].get_guard()
    negation_dict[key].make_negations(guard_list)
'''
# Only for busbar_IED
negation_dict = {}
matrix = final_xmldata["busbar_IED"].matrix
no_of_cond = final_xmldata["busbar_IED"].no_of_cond
negation_dict["busbar_IED"] = form_negations("busbar_IED", matrix, no_of_cond)
guard_list = negation_dict["busbar_IED"].get_guard()
negation_dict["busbar_IED"].make_negations(guard_list)


class create_global_variables():
    def __init__(self, name, matrix_list, no_of_cond, negated_guard_dict):
        self.name = name
        self.dict_matrix = matrix_list
        self.no_of_cond = no_of_cond
        self.negated_guard_dict = negated_guard_dict

    def get_raw_list(self):
        all_values = list(self.dict_matrix.values())
        merged_list = list(itertools.chain.from_iterable(all_values))
        merged_list = list(itertools.chain.from_iterable(merged_list))
        # drop duplicates
        final_list = list(dict.fromkeys(merged_list))
        return final_list

    def is_bool_numeric(self, b):
        if b.isnumeric():
            return True
        b_list = ["True", "TRUE", "true", "False", "FALSE", "false"]
        try:
            if b in b_list:
                return True
        except:
            return False

    def string_split(self, raw_list):
        split_string_list = []
        for str in raw_list:
            temp_var = str.strip()
            temp_var = temp_var.replace(" ", "")
            temp_split_var = re.split(',', temp_var)
            split_string_list.append(temp_split_var)
        split_string_list = list(itertools.chain.from_iterable(split_string_list))
        return split_string_list

    def is_counter(self, string):
        container = ["++", "+1", "+ 1"]
        try:
            for c in container:
                if c in string:
                    return True
        except:
            return False

    def get_variables(self):
        final_var_list = []
        final_list = self.get_raw_list()
        split_final_list = self.string_split(final_list)
        for st in split_final_list:
            var_temp = re.split('<(?!=)|<=|==|=(?!=)|>(?!=)|>=', st)
            if len(var_temp) == 2:
                #Check if the string after operator symbol is numeric or boolean
                if self.is_bool_numeric(var_temp[1]):
                    final_var_list.append(var_temp[0])
                elif self.is_counter(var_temp[1]):
                    final_var_list.append(var_temp[0])
                else:
                    final_var_list.append(var_temp[0])
                    final_var_list.append(var_temp[1])
            if len(var_temp) == 1:
                if self.is_counter(var_temp[0]):
                    final_var_list.append(var_temp[0].strip("++"))
        self.final_global_variables = final_var_list

## The for loop in dictionary is to be created. For time being only one variable is being used.
global_var_dict = {}
v1 = "busbar_IED"
v2 = negation_dict[v1].dict_matrix
v3 = negation_dict[v1].no_of_cond
v4 = negation_dict[v1].negated_guard_dict
global_var_dict[v1] = create_global_variables(v1, v2, v3, v4)
global_var_dict[v1].get_variables()
print("end")

class create_functions_bro():
    def __init__(self, name, matrix_list, no_of_cond, negated_guard_dict, final_global_variables):
        self.name = name
        self.dict_matrix = matrix_list
        self.no_of_cond = no_of_cond
        self.negated_guard_dict = negated_guard_dict
        self.final_global_variables = final_global_variables
        self.function_template = ""
        self.injection_template = ""
    def create_injection_function(self):
        print("To code")

functions_bro_dict = {}
v1 = "busbar_IED"
v2 = global_var_dict[v1].dict_matrix
v3 = global_var_dict[v1].no_of_cond
v4 = global_var_dict[v1].negated_guard_dict
v5 = global_var_dict[v1].final_global_variables
functions_bro_dict[v1] = create_functions_bro(v1, v2, v3, v4, v5)
print("end")


'''
#print(xml_dict['busbar_IED'].matrix[0])
#print(xml_dict['feeder_IED'].matrix[0])
print("end")
#Step 1: Form class using xml_data("Used names"). Maxtrix is formed using ids in one of template name
#Step 2: Find guard condition which has "!" which will return matrix with vectors. Currently, it is expected to have
#only one guard condition with "!"
'''