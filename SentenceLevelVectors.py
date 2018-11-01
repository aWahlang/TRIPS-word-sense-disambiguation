import sys
sys.path.append(".")
import re
import pandas as pd
import numpy as np
from os import listdir
from vectors import parseFeqDep1, load_obj
from Helpers.OutfileParsingHelpers import genDeplist

#function to create a binary vectors for each sentece of a nounOut file
#As of now the function is  designed to work with outfiles, make sure the outfile is named [noun]Out.csv
#root -> path to the directory that contains the outfiles
#senteence_count -> number of sentence to turn into vectors enter None for all sentence in the outfile
#feqDir -> path to the directory that contains the frequent itemsets for the noun 
#noun -> noun in lower case

def createSentenceLevelVec(root, saveDir, noun, sentence_count, feqDir=None, random_sample = False):
    feqFiles = listdir(feqDir)
    if(feqDir == None ):
        #porblem vector maps are out of date
        feq1 = list(load_obj('vector_map_detSplit').keys())
    else:
        file = [x for x in feqFiles if re.search('^' + noun+'_FeqDep', x)]
        print(file[0] + ' used as vector map...')
        feq1 = parseFeqDep1(feqDir + file[0])

    #vector columns names
    cols = ['Sentence','Noun', 'NN', 'NNS', 'NNP','NNPS', 'VB', 'VBG','VBP','VBZ','VBN','VBD', 'Verb object', 'Verb subject',\
            'singular', 'plural', 'bare singular', 'bare plural', 'bare linked', 'countable', 'uncountable'] + feq1
    outFile = pd.read_csv(root+noun+'Out.csv')
    if(sentence_count == None):
        sentence_count = outFile.shape[0]
    vectors = pd.DataFrame('0', index= np.arange(sentence_count), columns= cols)
    
    #function to add attribute to vector row
    def addToVec(row, att, val):
        if(att in cols):
            vectors.at[row, att] = val
        else:
            print('New Attribute: ' + att)

    #Randon Sampling
    if(random_sample):
        outFile = outFile.sample(n=sentence_count)
    #vector row count    
    c = 0
    rCount = 0

    for row in range(outFile.shape[0]):
        sen = outFile.at[row, 'Sentence']
        #skip is bad sentence or Right compounds 
        if('@ @ @ @ @ @' in sen or not outFile.at[row,'Right Compounds'] == '[]'):
            rCount += 1
            continue
        depSplit = outFile.at[row, 'Relevant Dependencies']
        if(pd.isnull(depSplit)):
            continue
        else:
            depSplit = depSplit.split()
            
        currentNoun = outFile.at[row, 'Noun']
        deps = genDeplist(depSplit, True, [currentNoun])
        
        #adding Sentence, Noun, NounTag,to vector
        addToVec(c, 'Sentence', sen)
        addToVec(c, 'Noun', currentNoun)
        addToVec(c, outFile.at[row, 'Noun Tag'], '1')
        verbTag = outFile.at[row, 'Verb Tag']
        #adding VerbTag to vector
        if(not pd.isnull(verbTag) and verbTag in ['VB', 'VBG','VBP','VBZ','VBN','VBD']):
            addToVec(c, verbTag, '1')
            relation = outFile.at[row, 'Relation to Verb']
            addToVec(c, 'Verb '+relation, '1')
        #adding plurality of noun to vector
        plurality = outFile.at[row, 'Plurality of Noun']
        addToVec(c, plurality, '1')
        #adding bareness of noun to vector
        nb = outFile.at[row, 'Bareness of Noun']
        if(nb == 'linked'):
            addToVec(c, 'bare linked', '1')
        else:
            addToVec(c, nb, '1')
        #adding countability to vector
        countability = outFile.at[row, 'Countability']
        if(not countability == 'unknown'):
            addToVec(c, countability, '1')
        #adding frequent dependancies of noun to vector
        for val in deps:
            if(val in feq1):
                addToVec(c, val, '1')

        c +=1
        if(c == sentence_count):
            break

    # drop empty rows 
    vectors = vectors.drop(vectors[vectors.Sentence == '0'].index)
    print("Rows skipped:" + str(rCount))
    fName = saveDir + noun + 'SentenceVectors.csv'
    vectors.to_csv(fName, index = False)
    print(fName+' saved')


#--------------------------------------------------
if __name__ == "__main__":
    root = '/Users/aeshaanwahlang/Documents/QuantitativeSemanticsData/outfile_3/'
    save = '/Users/aeshaanwahlang/Documents/CourseWork/NLU/TRIPS/project/SentenceVectors'
    feq = '/Users/aeshaanwahlang/Documents/QuantitativeSemanticsData/FrequentDependancies/v1.5/Unique/Support_10/'
    nouns = ['friday', 'wednesday', 'autumn', 'ten', 'april', 'geologist']
    # for n in nouns:
    #     createSentenceLevelVec(r,s,n,100,f)

    # createSentenceLevelVec(r,s,'bat',None)