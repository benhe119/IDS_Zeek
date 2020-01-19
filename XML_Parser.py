# Library imports
import os
import xml.etree.ElementTree as ET
import lxml.etree
import xmltodict


# Get directory for all the XMLs files
path = './XMLs'
# Notes on XML parsing
# <name x="5" y="5">busbar_IED</name>
# name is tag, x="5" y="5" is attrib, busbar_IED is text. P
data_xml = []

#xml_file = ET.parse(path+"/Test_Busbar.xml")
xml_file = lxml.etree.parse(path+"/Test_Busbar.xml")
root_xml = xml_file.getroot()

# Function to get names of templates
def get_names(xml):
    names = []
    for elem in xml.findall(".//template/name"):
        names.append(elem.text)
        print(elem.text)
    return names

class xml_data():
    def __init__(self, name):
        self.name= name
        self.node = root_xml.find(".//template[name='{}']".format(self.name))

    def loc_data(self, id, tag):
        # test = xml.xpath("//*[(text()='busbar_IED')]") #get location of the node
        #node = root_xml.find(".//template[name='{}']".format(self.name))
        loc_node = self.node.findall(".//location[@id='{a}']/{b}".format(a=id, b=tag))
        if loc_node[0].text == None:
            print("Error! No value output with given ID and Tag in {}".format(self.name))
            exit()
        else:
            return loc_node[0].text

    def trans_data(self, src,tgt):
        find_src = self.node.findall(".//source[@ref='{}']/..".format(src))
        find_tgt = self.node.findall(".//target[@ref='{}']/..".format(tgt))
        finder = find_src or find_tgt
        if len(finder) == None:
            print("Error! No values found with given source and target in {}".format(self.name))
            exit()
        else:
            value = finder[0].find(".//label")
            return



l1 = xml_data("busbar_IED")
s1 = l1.loc_data(id = "id0", tag = "name")
s2 = l1.trans_data(src="id0", tgt="id2")




'''

def get_loc(xml, names):
    loc_data = {}
    for name in names:
        local_data = {}
        #test = xml.xpath("//*[(text()='busbar_IED')]") #get location of the node
        loc_node = xml.xpath(".// *[child::*[(text()='{}')]]".format(name))
        for loc in loc_node:
            value = []
            for x1 in loc:
                if x1.tag=="location":
                    for x2 in x1:
                        value.append((x2.tag, x2.text))
                        local_data[x1.attrib["id"]] = value
                        loc_data[name] = local_data
    return loc_data

def get_loc1(xml, id, name):
    #test = xml.xpath("//*[(text()='busbar_IED')]") #get location of the node
    node = xml.find(".//template[name='{}']".format('busbar_IED'))
    loc_node = node.findall(".//location[@id='{a}']/{b}".format(a= id,b= name))

    for loc in loc_node:
        value = []
        for x1 in loc:
            if x1.tag=="location":
                for x2 in x1:
                    value.append((x2.tag, x2.text))
                    local_data[x1.attrib["id"]] = value
                    loc_data[names] = local_data
    return loc_data

def get_transitions(xml, names):
    print("to code")

xml_names = get_names(root_xml)
loc_data = get_loc(root_xml, xml_names)
loc_data = get_loc1(root_xml, "id0", "busbar_IED")
trans_data = get_transitions(root_xml, xml_names)



for child in root_xml:
        val = {}
        sub_vec = []
        names = []
        if child.text == None or child.text == '\n':
            for x1 in child:
                if x1.text == None or x1.text == '\n':
                    for x2 in x1:
                        val[x2.tag]=x2.text
                else:
                    val[x1.tag] = x1.text
                sub_vec.append(val)

        else:
            val[child.tag] = child.text

        data_xml.append(val)

def get_edges(src, dst, name):
    x1 = root_xml.findall("template")
    print(src, dst, x1)

get_edges("id0", "id1", "busbar_IED")



# Get directory for all the XMLs files
path = './XMLs'
# Notes on XML parsing
# <name x="5" y="5">busbar_IED</name>
# Name is tag, x="5" y="5" is attrib, busbar_IED is text. P
data_xml = []
for filename in os.listdir(path):
    xml_file = ET.parse(path+"/"+filename)
    root_xml = xml_file.getroot()
    for child in root_xml:
        child_val = {}
        if child.text == None or child.text == '\n':
            for sub in child:
                if sub.text == None or sub.text == '\n':
                    for ssub in sub:
                        child_val[ssub.tag]=ssub.text
                else:
                    child_val[sub.tag] = sub.text
        else:
            child_val[child.tag] = child.text

        data_xml.append(child_val)
        data_xml = [{"".join(key.splitlines()): "".join(item.splitlines()) for key, item in my_dict.items()
                       if item is not None} for my_dict in data_xml]

print(data_xml)


## Dictionary method for xml values
xml_file = open(path+"/"+filename).read()
xml_dict = xmltodict.parse(xml_file)
xml_dict = testDict = {key: value.strip() for key, value in xml_dict.items()}
print(xml_dict['nta']['declaration'])


'''

