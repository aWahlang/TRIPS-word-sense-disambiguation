import sys
sys.path.append(".")
import pickle
import pandas as pd
import numpy as np
from os import listdir
from Helpers.progressbar import printProgressBar

#save any Object to ./obj/   
def save_obj(obj, name ):
    with open('obj/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
    print("Object saved")
    
#laod objet from ./obj/
def load_obj(name ):
    with open('obj/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)

#parse Frequent Relevant Dependancies of Size 1
def parseFeqDep1(path):
    dep = []
    with open(path, 'r') as f:
        values = f.readline()
    
    values = values.split(',')
    for val in values:
        if(not 'Frequent Itemset size' in val and not '%' in val and not val == '\n' and not val == ''):
            dep.append(val.replace(';', ''))
    
    return dep
#parse Frequent Relevant Dependancies of all sizes    
def parseFullFeqDep(path):
    dep = []
    with open(path, 'r') as f:
        content = f.readlines()
    
    for line in content:
        values = line.split(',')
        for val in values:
            if(not 'Frequent Itemset size' in val and not '%' in val and not val == '\n' and not val == ''):
                dep.append(val)
    
    return dep

#Create vector map
def genVectorMap(minSup, path, full = False):
    vmap = {}
    path += str(minSup) + '/'
    files = listdir(path)
    vcount = 1
    fcount = 0
    printProgressBar(0,20,prefix = 'Progress:', suffix = 'Completed', length = 20)
    for f in files:
        if(full):
            data =  parseFullFeqDep(path + f)
        else:
            data = parseFeqDep1(path + f)

        #REDUNDANT MUST UPDATE     
        for val in data:
            val = val.replace(';' , ' ')
            val = val.strip()
            val = val.replace(' ' , ',')
            if(not val in vmap.keys()):
                vmap[val] = vcount
                vcount += 1
        
        fcount +=1
        if(fcount % int(len(files)/20) == 0):
            printProgressBar(fcount/100,20,prefix = 'Progress:', suffix = 'Completed', length = 20)
    
  

    if(full):
        save_obj(vmap, 'vector_map_full_detSplit')
    else:
        save_obj(vmap, 'vector_map_detSplit')
#    print(vmap)
    print("size:" + str(vcount-1))
    if('compound-left' in vmap ):
        print("compound-left in vector map")

 
#create vectors represenation for frequent Revelevant Dependancies based on support
def createVectors(minSup, path, full = False):
    path += str(minSup) + '/'
    master = pd.read_csv('C:/Users/Aeshaan Wahlang/Documents/CourseWork/Summer/Linguistics/new_master_all_info_join_celex3.csv')
    mlook = ['countable', 'uncountable']
    files = listdir(path)
    
    if(not full):
        vmap = load_obj('vector_map_detSplit')
    else:
        vmap = load_obj('vector_map_full_detSplit')
        
    cols = ['Noun'] + list(vmap.keys()) + mlook
    #create dataframe for vectors 
    vectors = pd.DataFrame('0', index = np.arange(len(files)), columns = cols)   
    count = 0
    l = len(vmap.keys())
    
    for att in mlook:
        vmap[att] = l
        l +=1
       
    def getNoun(filename):
        index = filename.find('_')
        noun = filename[:index]
        return noun
    
    def getDep(dic, path, full):
        items = []
        if(not full):
            with open(path, 'r') as f:
                items = f.readline()
            items = items.split(',')
        else:
            with open(path, 'r') as f:
                content = f.readlines()
            for line in content:
                split = line.split(',')
                items += split
            
        for i in range(len(items)):
            if(not 'Frequent Itemset size' in items[i] and not items[i] == '\n'):
                if(';' in items[i]):
                    dep = items[i].replace(';',' ')
                    dep = dep.strip()
                    dep = dep.replace(' ', ',')
                    val = items[i+1].replace('%','')
                    val = float(val)/100
                    dic[dep] = round(val,3)
                else:
                    continue
        return dic
    
    def lookup(master, noun, att, dic):
        if(noun == 'nan'):
            dic[att] = 0
            return
        idx = master.index[master['Noun'] == noun].tolist()
        val = master.iloc[idx][att]
        if(val.values[0] == 'Y'):
            dic[att] = 1
        else:
            dic[att] = 0
            
    printProgressBar(0,24,prefix = 'Progress:', suffix = 'Completed', length = 24)
    for f in files:
        info = {}
        info['Noun'] = getNoun(f)
        getDep(info, path + f, full)
        
        for att in mlook:
           lookup(master, info['Noun'], att, info) 
        
        for key in info:
#            idx = vmap[key]
            vectors.iloc[count][key] = info[key]

        count +=1
        if(count % 100 == 0):
            printProgressBar(count/100,24,prefix = 'Progress:', suffix = 'Completed', length = 24)
            
    if(not full):
        filename = 'FeqRelDependanciesVector_detSplit_' + str(minSup) +'.csv'
    else:
        filename = 'FeqRelDependanciesVectorFull_detSplit_' + str(minSup) +'.csv'
    vectors.to_csv(filename, index = False)
    print(filename + ' saved')
    
   

        
#RUN-----------------------------------------------------------------
##
#genVectorMap(10, path ='F:/LinguisticsData/FrequentDependancies/RightCompounds/temp/NonUnique/Support_', full = True)
#
#createVectors(10,'F:/LinguisticsData/FrequentDependancies/RightCompounds/temp/NonUnique/Support_',  full = True)
