import os
import xml.etree.ElementTree as et
import time

from xml.etree.ElementTree import Element, ElementTree

def openxml(filename):

    with open(filename, 'r', errors = 'ignore') as f:
        file = f.read()

    register_namespaces(file)

    root = et.parse(filename).getroot()
    return root

def register_namespaces(file):
    start = file.find('Structure') + 10
    end = file[start:].find('>') + start
    structure = file[start:end]
    
    namespaces = {}
    start = structure.find('"') + 1

    while start != 0:
        end = structure[start:].find('"') + start

        namespace_start = structure[:start].rfind(':') + 1
        namespace_end = structure[namespace_start:].find('=') + namespace_start

        namespace = structure[namespace_start:namespace_end]
        uri = structure[start:end]
        namespaces[namespace] = uri
        
        structure = structure[end+1:]        
        start = structure.find('"') + 1

    del namespaces['schemaLocation']
    for ns in namespaces:
        et.register_namespace(ns, namespaces[ns])

def remove_version_str(urn):
    try:
        start = urn.rfind('(')
        end = urn.rfind(')') + 1

        _ = float(urn[start + 1:end - 1])

        if start == -1 or end == -1:
            return urn
        else:
            return urn[:start] + '(1.0)' + urn[end:]
    except Exception:
        return urn

def remove_version_et(obj):
    try:
        urn = remove_version_str(obj.attrib['urn'])
        new_obj = obj
        new_obj.attrib['urn'] = urn
        return new_obj
    except:
        return obj


def main(filename):
    rt = openxml(filename)
    _, keyfamilies = list(rt)
    last_id = ''

    for keyfamily in reversed(keyfamilies):
        if last_id == keyfamily.attrib['id']:
            keyfamilies.remove(keyfamily)
        else:
            keyfamily = remove_version_et(keyfamily)
            keyfamily.attrib['version'] = '1.0'
            keyfamily.attrib['isFinal'] = 'true'
        last_id = keyfamily.attrib['id']

    for keyfamily in keyfamilies:
        for component in keyfamily:
            for dimension in component:
                try:
                    dimension.attrib['conceptVersion'] = '1.0'
                except:
                    pass
                try:
                    dimension.attrib['codelistVersion'] = '1.0'
                except:
                    pass
        
    final_string = et.tostring(rt)
    with open('new_' + filename, 'wb') as f:
        f.write(final_string)


main('datastructure.xml')