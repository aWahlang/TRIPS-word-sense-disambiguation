#Helper methods to parse elements of Outfiles
import string
import re
import pandas as pd

#method to remove punctuations and digits from a dependency string
#s - string to clean
def cleanDep(s):    
    #translators to remove punctuation and digits
    translator = str.maketrans(dict.fromkeys(string.punctuation))
    translator2 = str.maketrans(dict.fromkeys(string.digits))
    s = s.translate(translator)
    s = s.translate(translator2)

    return s

#method to check if strings in list l is present in string s
def isPresent(l, s):
    for val in l:
        if (re.search(val, s, re.IGNORECASE)):
            return True
    return False

#group determiner type
#val - det dependency string
def group_det(val):
    g1 = ['det-the', 'det-that', 'det-this', 'det-some', 'det-any', 'det-those', 'det-these',
            'det-both', 'det-another', 'det-every', 'det-each', 'det-which', 'det-either',
            'det-all', 'det-what']
    g2 = ['det-a', 'det-an']
    g_qmod1 = ['det:qmod-hundreds', 'det:qmod-thousands', 'det:qmod-millions', 'det:qmod-billions',
            'det:qmod-dozen' ]
    g_qmod2 = ['det:qmod-a', 'det:qmod-an']
    
    if('det:qmod' in val):
        if(val in g_qmod1):
            return 'det:qmod-numeral'
        if(val in g_qmod2):
            return 'det:qmod-a/an'
        else:
            return 'det:qmod-other'
    else:
        if(val in g1):
            return val
        if(val in g2):
            return 'det-a/an'
        else:
            return 'det-other'


#method to parse dependency row to a list
#split - list of dependencies split on ' ' unique - boolean for unique counts
def genDeplist(split, unique, nouns):
    deplist = []
    for i in range(len(split)):
        val = split[i]
        index = val.find('(')
        if(index != -1):
            dep_val = val[0:index]
            val = val.lower()
            if(dep_val == 'det' or 'det:' in dep_val):
                if(isPresent(nouns, val)):
                    dep_val +='-' + cleanDep(split[i+1].lower())
                else:
                    dep_val +='-' + cleanDep(val.replace(dep_val, '').lower())
                
                deplist.append(group_det(dep_val))
            else:
                deplist.append(dep_val)

    if(unique):            
        deplist = list(set(deplist))
    return deplist
            



#Parse Relevant Depedencies while spilitting 'det' and 'compounds'
def parseRelDep(data, unique = True, includeRightCompound = False):
    dic = {}
    count = 0
    nouns = set(data['Noun'].tolist())
         
    for row in range(data.shape[0]):
        dependencies = data.iloc[row,'Relevant Dependencies']
        if(not pd.isnull(dependencies) and data.iloc[row, 'Right Compounds'] == '[]' ):
            split = str.split(dependencies)
        else:
            continue
        dList = genDeplist(split, unique, nouns)
        dic[count] = dList
        count += 1
    return dic


