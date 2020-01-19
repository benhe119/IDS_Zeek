# Library imports
import lxml.etree
import re
import numpy as np
from itertools import permutations
import pandas as pd
import threading

# Get directory for all the XMLs files
path = './XMLs'
# Notes on XML parsing
# <name x="5" y="5">busbar_IED</name>
# name is tag, x="5" y="5" is attrib, busbar_IED is text. P

#xml_file = ET.parse(path+"/Test_Busbar.xml")
xml_file = lxml.etree.parse(path+"/Test_Busbar.xml")
root_xml = xml_file.getroot()


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False

def is_bool(b):
    b_list = ["True", "TRUE", "true", "False", "FALSE", "false"]
    try:
        if b in b_list:
            return True
    except:
        return False

#Getting global declaration
data_types = ["int", "char", "bool", "clock", "chan"]
global_dec = [elem.text for elem in root_xml.findall(".//declaration") if elem.text!=None][0]
global_dec = ([var for var in global_dec.split("\n") if "//" not in var]) #Removing the comments from the global declaration
temp_dict ={}
for var in global_dec:
    var = (re.findall(r"[\w']+", var))
    if len(var) > 2:
        if is_number(var[2]):
            temp_dict[var[1]] = 0
        elif is_bool(var[2]):
            temp_dict[var[1]] = False
        else:
            var = var[1:]
            for v in var:
                temp_dict[v] = ""
global_dec = temp_dict
print(global_dec)

class form_data():
    def __init__(self, id_a, id_b):
        self.id_a = id_a
        self.id_a = id_b

class xml_data():
    def __init__(self, name):
        self.name = name
        self.node = root_xml.find(".//template[name='{}']".format(self.name))
        self.id_names = self.get_ids()

    def local_declaration(self):
        print("To code")

    def get_ids(self):
        find_src = self.node.findall(".//source")
        find_tgt = self.node.findall(".//target")
        ids = [at.attrib["ref"] for at in find_src]
        ids.extend([at.attrib["ref"] for at in find_src])
        id_names = sorted(set(ids))
        return id_names

    def get_data_old(self):
        perm = list(permutations(self.id_names, 2))
        r_index = [id[0]+id[1] for id in perm]
        c_names = set([elem.attrib["kind"] for elem in self.node.findall(".//*[@kind]")])
        df_xml = pd.DataFrame(index= r_index, columns = c_names)

        for src_tgt in perm:
            finder = (self.node.findall(".//source[@ref='{}']/..target[@ref='{}']/..".format(src_tgt[0], src_tgt[1])))
            #finder = (self.node.findall(".//source[@ref='{}']/..".format(src_tgt[0])) or
            #         self.node.findall(".//target[@ref='{}']/..".format(src_tgt[1])))
            row_name = src_tgt[0]+src_tgt[1]
            if finder is None:
                continue
            else:
                for x in finder:
                    for y in x:
                        print(y.attrib)
                    for elem in x.findall(".//*[@kind]"):
                        df_xml.at[row_name, [elem.attrib["kind"]]]= elem.text
                        print(elem.attrib["kind"])
        print("B1")

    def get_data(self):
        idx = {}
        temp_cnt = 0
        for id in self.id_names:
            idx[id] = temp_cnt
            temp_cnt = temp_cnt + 1
        dim_names = set([elem.attrib["kind"] for elem in self.node.findall(".//*[@kind]")])
        dim = {}
        temp_cnt = 0
        for d in dim_names:
            dim[d] = temp_cnt
            temp_cnt = temp_cnt + 1
        m_matrix = np.zeros((len(dim), len(self.id_names), len(self.id_names)), dtype=object) # no. of Dimension, row, colmuns
        perm = list(permutations(self.id_names, 2))
        for src_tgt in perm:
            finder = (self.node.findall(".//source[@ref='{}']/..target[@ref='{}']/..".format(src_tgt[0], src_tgt[1])))
            #finder = (self.node.findall(".//source[@ref='{}']/..".format(src_tgt[0])) or
            #         self.node.findall(".//target[@ref='{}']/..".format(src_tgt[1])))
            idx_0 = idx[src_tgt[0]] #Row index
            idx_1 = idx[src_tgt[1]] #Column index
            if finder is None:
                continue
            else:
                for x in finder:
                    #for y in x:
                    #    print(y.attrib)
                    for elem in x.findall(".//*[@kind]"):
                        #print(elem)
                        dimen = dim[elem.attrib["kind"]]
                        if (m_matrix[dimen, idx_0, idx_1]) is 0:
                            m_matrix[dimen, idx_0, idx_1] = elem.text
                        else:
                            temp_data = [m_matrix[dimen, idx_0, idx_1], elem.text]
                            m_matrix[dimen, idx_0, idx_1] = temp_data

                        #print(elem.attrib["kind"])
        #print(m_matrix)
        return m_matrix

    def find_tgt(self, vectors):
        if len(vectors) > 5:
            print(vectors)
            return vectors
        else:
            src = vectors[-1][1]
            finder = (self.node.findall(".//source[@ref='{}']/..".format(src)))
            if len(finder) > 0:
                tgt = finder[0].find(".//target").attrib["ref"]
                vectors.append((src, tgt))
            #print(tgt)
            #print(vectors)
        self.find_tgt(vectors)


    def form_vectors(self):
        perm = list(permutations(self.id_names, 2))
        vectors = {}
        temp_cnt = 0
        for src_tgt in perm:
            self.find_tgt([src_tgt])


        print("end")



# Function to get names of templates
def get_names(xml):
    names = []
    for elem in xml.findall(".//template/name"):
        names.append(elem.text)
        #print(elem.text)
    return names

# Getting the names from XML file
xml_names = get_names(root_xml)
#print(xml_names)

# Making Class type for each names and storing it dictionary
xml_values = {}
for name in xml_names:
    xml_values[name] = xml_data(name)

#Testing code
l1 = xml_data("busbar_IED")
l2 = xml_data("feeder_IED")
s1 = l1.get_ids()
s2 = l1.form_vectors()
s3 = l1.get_data()
s4 = l2.get_data()
print(s2)
#print(s3)

#print(s4)

print("end")