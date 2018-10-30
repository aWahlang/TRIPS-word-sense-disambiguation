# -*- coding: utf-8 -*-

import re
import ast
import csv
import os
# Encapsulates word lemma and tag information
class Tag:
    # Expects input in form of asked/ask/VBD
    # asked --> __word
    # ask --> __lemma
    # VBD --> __POS
    def __init__(self, rawTagString):
        self.__word, self.__lemma, self.__POS = rawTagString.split('/')
        
    # if POS is like NN*
    def isNoun(self):
        return self.__POS[0] == 'N' and self.__POS[1] == 'N'
    
    # Acessor Methods
    def getWord(self):
        return self.__word
    
    def getLemma(self):
        return self.__lemma
    
    def getPOS(self):
        return self.__POS
    
    # prints in the same format as the input string
    def __str__(self):
        return self.getWord() + '/' + self.getLemma() + '/' + self.getPOS()
    def __repr__(self):
        return str(self)
    # factory-ish method for generating many tag objects from a space separated string of tags
    def generateTags(tagsFromCSV):
        tagStrings = tagsFromCSV.split(' ')
        tags= []
        for tag in tagStrings:
            tags.append(Tag(tag))
        return tags

    
# Encapsulates depdency type and both words in the relationship
class Dependency:
    # Expects input in the form dobj (left-4, right-7)
    # dobj --> __type
    # left --> __head
    # right --> __dependent
	
    def __init__(self, rawDepString):
        # string splits into ['dobj', '(left-4,','right-7)']
        t,h,d = rawDepString.split(' ')
        self.__type = t
        self.__head = Word(h[1:-1]) # remove paren and comma
        self.__dependent = Word(d[:-1]) # remove paren
        
        pref = t[:4]
        self.__subType = ''
        if pref == 'conj': # example: "conj:and"
            self.__subType = self.__type[5:] # set subtype to value after "conj:"
            self.__type = pref # set to "conj" no colon
        elif pref == 'nmod': # example: "nmod:of"
            self.__subType = self.__type[5:] # set subtype to value after "nmod:"
            self.__type = pref # set to "nmod" no colon
        elif pref == 'det:': # example: "det:the"
            self.__subType = self.__type[4:] # set subtype to value after "det:"
            self.__type = pref[:3] # set to "det"

    
    # returns true if the word matches a string comparison of the head or dependent word
    def hasWord(self, word):
        return self.__head.getToken() == word or self.__dependent.getToken() == word
    
    # returns true if the index matches either the head or dependent word
    def hasIndex(self, index):
        return self.isHead(index) or self.isDependent(index)
    
    # returns true if the wordIndex is our head word/ 'left' word
    def isHead(self, wordIndex):
        return self.__head.getIndex() == wordIndex
		
    # returns true if the wordIndex our dependent word/ 'right' word
    def isDependent(self, wordIndex):
        return self.__dependent.getIndex() == wordIndex
    
    # Acessor Methods
    
    # returns type such as 'nsubj' or type and subtype if a subtype exists returns 'conj:and'
    def getType(self):
        if self.__subType == '':
            return self.__type
        else:
            return self.__type + ':' + self.__subType
    
	# returns without subtype, used for generating dictionaries that use the type as the key
    def getDependencyRelationship(self):
        return self.__type
    
    def getSubType(self):
        return self.__subType
    
    def getHead(self):
        return self.__head
    
    def getDependent(self):
        return self.__dependent
    
    def __str__(self):
        return self.getType() + ' (' + self.getHead().__str__() + ', ' + self.getDependent().__str__() + ')'
    
    def __repr__(self):
        return str(self)
    
    def generateDependencies(depsFromCSV):
        deps = re.findall(r"(\S* \(\S*-[0-9]*, \S*-[0-9]*\))",depsFromCSV)
        listOfDependencies = []
        for dep in deps:
            listOfDependencies.append(Dependency(dep))
        
        return listOfDependencies

class Word:
    def __init__(self, rawString):
        endOfToken = rawString.rfind('-')#find the - splitting the token and index
        self.__token = rawString[:endOfToken] # string before last "-"
        self.__index = int(rawString[endOfToken+1:]) # string after and including last "-"

        
    def getToken(self):
        return self.__token
    
    def getIndex(self):
        return self.__index
    
    def __str__(self):
        return self.getToken() + '-' + str(self.getIndex())
    def __repr__(self):
        return str(self)
# Encapsulates the sentence, passageID number, the tags, and dependencies
class Raw:
    def __init__(self, line):
        self.__sentence = line[0]
        tags = line[1]
        parse = line[2]
        self.__sentID = line[4]
        self.__passageID = line[5]
        self.__rawNER = line[3]
		
        self.__tags = Tag.generateTags(tags)
        
        self.__dependencies = Dependency.generateDependencies(parse)
        self.__dependenciesDict = {}
        
        for dep in self.__dependencies:
            key = dep.getDependencyRelationship()
            if key in self.__dependenciesDict:
                self.__dependenciesDict[key].append(dep)
            else:
                self.__dependenciesDict[key] = [dep]
        
        # Assuming coref data is stored at 9th column
        if len(line) > 6:
            self.__coref = ast.literal_eval(line[6])
            self.__hasCoref = True
        else:
            self.__hasCoref = False
                
	# Acessor Methods
    def getTags(self):
        return self.__tags
    
    def getSentence(self):
        return self.__sentence
	
    def getDependencies(self):
        return self.__dependencies
    
    def getDependenciesAsDict(self):
        return self.__dependenciesDict
    
    def getRawNER(self):
    		return self.__rawNER
	
    def getSentID(self):
        return int(self.__sentID)
    
    def getPassageID(self):
        return self.__passageID

    def containsCoref(self):
        return self.__hasCoref
    
    def getCoref(self):
        if not self.__hasCoref:
            return None
        else:
            return self.__coref
        
class NounAnalysis:
    # rawSentence should be a Raw object
    # nounTag should be the Tag object for the noun to analyze
    # nounIndex should be the index of the Tag for the noun to analyze
    def __init__(self, rawSentence, nounTag, nounIndex):
        self.__sentence = rawSentence
        self.__noun = nounTag.getLemma()
        self.__nounIndex = nounIndex
        self.__nounPOS = nounTag.getPOS()
        
        self.__relevantDependencies = NounAnalysis.generateRelevantDependencies(rawSentence.getDependencies(), nounIndex)

        # dictionaries generated for quick indexing within analysis methods
        allDepDict = rawSentence.getDependenciesAsDict()
        relDepDict = NounAnalysis.getRelevantDependenciesAsDict(self.__relevantDependencies)
        
        # Analysis
        self.__negDeps = self.getNeg(nounIndex, relDepDict)
        
        # Values for the verb, verbPOS, relation of our noun to verb, verb lemma, list of any Aux for verb
        # isCopula is used to detect if the noun is associated to the verb via a copula relationship
        verb, self.__verbPOS, self.__relationToVerb, self.__verbLemma, \
        self.__aux, isCopula = self.getVerb(nounIndex, relDepDict, allDepDict)
        
        if isCopula: # replace verb items with copula information and populate copula specific columns
            verb, self.__relationToVerb, self.__verbPOS, self.__copOtherPOS, self.__aux = self.getCopula(nounIndex, relDepDict, allDepDict)
            self.__verbLemma = ''
        else:
            self.__copOtherPOS = ''
        
        if verb:
            self.__verbNeg = self.getNeg(verb.getIndex(), allDepDict)
            self.__verbAdvMod = self.getAdv(verb.getIndex(), allDepDict)
            self.__cond = self.getCondOfN(nounIndex, verb, relDepDict, allDepDict)
            self.__modal = self.getModal(verb, allDepDict)
        else:
            self.__verbNeg = []
            self.__verbAdvMod = []
            self.__cond = []
            self.__modal = []
        self.__verb = verb
        
        # set determiner and determiner type
        self.__detType, self.__detDeps = self.getDet(nounIndex, relDepDict)
        
        # set conjoined, conjunction phrases, conjunctions
        # isBareShortCut is a boolean flag to save work if our noun is the left side of the conjunction relationship
        self.__conjoined, self.__conjunctionPhrases, self.__conjunctions, isBareShortCut = self.getConj(nounIndex, relDepDict)
         
        # set compoundHead, and Mod
        self.__compoundHead, self.__compoundMod = self.getCompound(nounIndex, relDepDict)
        
        # Possesivity and prepositions all analyzed at once for efficiency due to all being based on the nsubj depdency
        # set possessed, possessive, and preposition info
        self.__possessed, self.__possessive, self.__prepSubjects, self.__prepObjects, \
        self.__prepPhrases, self.__prepositions = self.getNmod(nounIndex, relDepDict)
        
        # set nummeric modifier (SORT of SKETCHY, Intelligently improve later)
        self.__nummod = self.getNummod(nounIndex, relDepDict)
        
        # set case infoz
        self.__case = self.getCase(nounIndex, relDepDict)
        
        # set advmod for our noun
        self.__adv = self.getAdv(nounIndex, relDepDict)
        
		
        self.__adjs = self.getAdjs(nounIndex, relDepDict)
        self.populateAdjTypes()
        
		
        self.__appos, self.__modifiedAppos, self.__modifierAppos = self.getAppos(nounIndex, relDepDict)
        
        
        
        
        
        self.__pluN = self.isPluralN(nounTag)
        
        self.__pluV = self.isPluralV(self.__verbPOS)
		
        self.__denumerator, self.__denType = self.getDenumerator(self.__detDeps, self.__adjs)
		
        self.__bare = self.isBare(self.__pluN, self.__conjoined, rawSentence.getDependencies(), isBareShortCut)

        # get coref info
        if self.__sentence.getCoref():
            #self.__coref = 
            self.__lenOfChain, self.__isHead, self.__isCorrupted, self.__absLocInChain, self.__relLocInChain, self.__distFromPrevMen = self.getCorefs(self.__sentence.getSentID(), self.__sentence.getCoref())
        else:
            self.__lenOfChain = ''
            self.__isHead = ''
            self.__isCorrupted = ''
            self.__absLocInChain = ''
            self.__relLocInChain = ''
            self.__distFromPrevMen = ''
            #self.__coref = []
        
    # for each relevant dependency of type 'neg' 
    # if the head word's index matches the nounIndex
    # then add the token of the DEPENDENT word to the list negDeps
    def getNeg(self, nounIndex, relDepDict):
        negDeps = []
        if 'neg' in relDepDict:
            for negDep in relDepDict['neg']:
                if negDep.isHead(nounIndex):
                    negDeps.append(negDep.getDependent().getToken())
        return negDeps        
        
    def getVerb(self, nounIndex, relDepDict, allDepDict):
        
        if 'dobj' in relDepDict:
            
            relationToVerb = 'object'
            # Should never be more than one in relevant dependencies
            dependency = relDepDict['dobj'][0]
            verb = dependency.getHead()
            
        elif 'nsubjpass' in relDepDict:
            
            relationToVerb = 'passive'
            # Should never be more than one in relevant dependencies
            dependency = relDepDict['nsubjpass'][0]
            verb = dependency.getHead()
            
        elif 'iobj' in relDepDict:
            
            relationToVerb = 'object'
            # Should never be more than one in relevant dependencies
            dependency = relDepDict['iobj'][0]
            verb = dependency.getHead()
            
        elif 'nsubj' in relDepDict:
            
            relationToVerb = 'subject'
            # Should never be more than one in relevant dependencies
            dependency = relDepDict['nsubj'][0]
            verb = dependency.getHead()
            
        else:
            # no verb, no verbPOS, no relationToVerb, no verbLemma, is not CopulaVerb
            return '', '', '', '', [], False
        verbTag = self.getTagFromIndex(verb.getIndex())#__sentence.getTags()[verb.getIndex() - 1]
        
        if verbTag.getPOS() not in verbPOSs:
            # no verb, no verbPOS, no relationToVerb, no verbLemma, no auxList isCopulaVerb
            return '', '', '', '', [], True
        
        verbLemma = verbTag.getLemma()
        #verbString = verb.getToken()
        auxList = self.getAux(verb, allDepDict)
        
        return verb, verbTag.getPOS(), relationToVerb, verbLemma, auxList, False # not CopluaVerb
        
        
    def getCopula(self, nounIndex, relDepDict, allDepDict):
        
        if 'cop' in relDepDict:
            copDep = relDepDict['cop'][0]
            if copDep.isHead(nounIndex):
                copula = copDep.getDependent()
                other = copDep.getHead()
            else:
                print("Hmmm, maybe wuh oh? getCopula")
            copula = copDep.getHead()
            other = copDep.getDependent()
            # retrieve the part of speech tag by indexing into the tag list
            copPOS = self.getTagFromIndex(copula.getIndex()).getPOS()
            copRelation = 'CopObject'
            otherPOS = self.getTagFromIndex(other.getIndex()).getPOS()
            auxList = self.getAux(other, allDepDict)
            return copula, copRelation, copPOS, otherPOS, auxList
        else:
            nsubjDep = relDepDict['nsubj'][0]
            
            if nsubjDep.isHead(nounIndex):
                copHead = nsubjDep.getDependent()
                print(nounIndex)
                print(self.getSentence().getSentence())
                print(self.__sentence.getDependencies())
            else:
                copHead = nsubjDep.getHead()
            if 'cop' in allDepDict:
                for copDep in allDepDict['cop']:
                    if copDep.isHead(copHead.getIndex()):
                        copula = copDep.getDependent()
                        other = copDep.getHead()
                        copPOS = self.getTagFromIndex(copula.getIndex()).getPOS()
                        otherPOS = self.getTagFromIndex(other.getIndex()).getPOS()
                        copRelation = 'CopSubject'
                        auxList = self.getAux(other, allDepDict)
                        return copula, copRelation, copPOS, otherPOS, auxList
            return '','','','',[]
    
    # verb needs to be a Word object
    def getAux(self, verb, allDepDict):
        auxList = []
        if 'aux' in allDepDict:
            for auxDep in allDepDict['aux']:
                if auxDep.isHead(verb.getIndex()):#getHead().getIndex() == verb.getIndex():
                    auxList.append(auxDep.getDependent().getToken())
        return auxList
    
    def getVerbNeg(self, verb, allDepDict):
        negList = []
        if 'neg' in allDepDict:
            for negDep in allDepDict['neg']:
                if negDep.isHead(verb.getIndex()):
                    negList.append(negDep.getDependent().getToken())
        return negList
    # for each relevant dependency of type 'nmod:X'
    # prepphrs <- (X, otherWord, otherWord's Index)
    # preps <- X
    # prepsubjs <- (if Head.isOurNoun) otherWord  
    # prepobjs <- (if Dependent.isOurNoun) otherWord
    def getNmod(self, nounIndex, relDepDict):
        possessive = []
        possessed = []
        prepObjects = []
        prepSubjects = []
        prepPhrases = []
        prepositions = []
        if 'nmod' in relDepDict:
            for modDep in relDepDict['nmod']:
                if modDep.getSubType() == 'poss':
                    if modDep.isHead(nounIndex):
                        possessive.append(modDep.getDependent().getToken())
                    else:
                        possessed.append(modDep.getHead().getToken())
                else:
                    if modDep.isHead(nounIndex):
                        word = modDep.getDependent()
                        prepObjects.append(word.getToken())
                    else:
                        word = modDep.getHead()
                        prepSubjects.append(word.getToken())
                    # list of tuples
                    prepPhrases.append((modDep.getSubType(), word.getToken(), word.getIndex()))
                    prepositions.append(modDep.getSubType())
        return possessive, possessed, prepObjects, prepSubjects, prepPhrases, prepositions
            
    def getDet(self, nounIndex, relDepDict):
        detType = []
        detDeps = []
        # for each dependency of type 'det' 
        # if the HEAD word's index matches the nounIndex
        # then add the token of the DEPENDENT word to the list detDeps
        if 'det' in relDepDict:
            for detDep in relDepDict['det']:
                if detDep.isHead(nounIndex):#getHead().getIndex() == nounIndex:
                    determiner = detDep.getDependent().getToken()
                    detType.append(NounAnalysis.getDeterminerType(determiner))
                    detDeps.append(determiner)
        
        return detType, detDeps
        
    def getConj(self, nounIndex, relDepDict):
        conjunctionPhrases = []
        conjunctions = []
        conjoinedList = []
        # for each dependency of type 'conj' 
        # the conjoined word is the one opposite the noun at nounindex
        # conjunction phrases list the conjunction, the conjoined word, and that word's index
        # the conjunction is held in the subtype, if it is a conj with no subtype (which happens)
        # then the empty string will be placed there.
        isBareShortCut = True # used in isBare to avoid a ton of work
        if 'conj' in relDepDict:
            for conjDep in relDepDict['conj']:
                if conjDep.isHead(nounIndex):#getHead().getIndex() == nounIndex:
                    conjoined = conjDep.getDependent()
                else: # Since these are relevant dependencies then the dependent must be the noun at nounindex
                    conjoined = conjDep.getHead()
                    isBareShortCut = False # used in isBare to avoid a ton of work
    				
                conjoinedList.append(conjoined)
                conjunctionPhrases.append((conjDep.getSubType(),conjoined.getToken(),conjoined.getIndex()))
                conjunctions.append(conjDep.getSubType())
                
        return conjoinedList, conjunctionPhrases, conjunctions, isBareShortCut
        
    def getCompound(self, nounIndex, relDepDict):
        compoundMod = []
        compoundHead = []
        
        if 'compound' in relDepDict:
            for compoundDep in relDepDict['compound']:
                if compoundDep.isHead(nounIndex):
                    compoundMod.append(compoundDep.getDependent().getToken())
                else:
                    compoundHead.append(compoundDep.getHead().getToken())
        
        return compoundHead, compoundMod
        
    def getAdjs(self, nounIndex, relDepDict):
        adjs = []
        if 'amod' in relDepDict:
            for amodDep in relDepDict['amod']:
                if amodDep.isHead(nounIndex): 
                    adjs.append(amodDep.getDependent().getToken())
        return adjs
    
    def populateAdjTypes(self):
        adjtype = getAdjType(self.__adjs)
        if adjtype:
            self.__adjbehav = list(adjtype[0])
            self.__adjbody = list(adjtype[1])
            self.__adjfeel = list(adjtype[2])
            self.__adjmind = list(adjtype[3])
            self.__adjmisc = list(adjtype[4])
            self.__adjmotion = list(adjtype[5])
            self.__adjpercep = list(adjtype[6])
            self.__adjquant = list(adjtype[7])
            self.__adjsocial = list(adjtype[8])
            self.__adjspatial = list(adjtype[9])
            self.__adjsubst = list(adjtype[10])
            self.__adjtemp = list(adjtype[11])
            self.__adjweather = list(adjtype[12])
        else: 
            self.__adjbehav = None
            self.__adjbody = None
            self.__adjfeel =  None
            self.__adjmind =  None
            self.__adjmisc =  None
            self.__adjmotion =  None
            self.__adjpercep =  None
            self.__adjquant =    None
            self.__adjsocial =  None
            self.__adjspatial =  None
            self.__adjsubst =    None
            self.__adjtemp =  None
            self.__adjweather =  None
        
    def getNummod(self, nounIndex, relDepDict):
        numericalModifier = []
        stack = []
        if 'nummod' in relDepDict:
            for nummodDep in relDepDict['nummod']:
                if nummodDep.isHead(nounIndex):
                    
                    # start at the element in the tags list one before the noun, and
                    # go backwards pushing any CD words onto the stack and ignoring 
                    # any CC words until a non CC/CD word is found after at least one
                    # has been found
                    for tag in reversed(self.__sentence.getTags()[:nounIndex-1]):
                        if tag.getPOS() == 'CD':
                            stack.append(tag.getLemma())
                        elif tag.getPOS() == 'CC':
                            continue
                        elif stack != []:
                            break
            # TODO LESS HACKY WAY DUMB DUMB
            while stack != []:
                numericalModifier.append(stack.pop())
        
        return numericalModifier
        
        
    def getCase(self, nounIndex, relDepDict):
        case = []
        if 'case' in relDepDict:
            for caseDep in relDepDict['case']:
                if caseDep.isHead(nounIndex):
                    case.append(caseDep.getDependent().getToken())
        return case
    
    def getAdv(self, nounIndex, relDepDict):
        adv = []
        if 'advmod' in relDepDict:
            for advDep in relDepDict['advmod']:
                if advDep.isHead(nounIndex):
                    adv.append(advDep.getDependent().getToken())
        return adv
        
    def getAppos(self, nounIndex, relDepDict):
        appos = []
        modifiedAppos = []
        modifierAppos = []
        # for each dependency of type 'appos'
        # if the head word's index matches the nounIndex
        # then add 'modified' and the other word
        # otherwise add 'modifier' and the head word
        if 'appos' in relDepDict:
            for apposDep in relDepDict['appos']:
                if apposDep.isHead(nounIndex):
                    word = apposDep.getDependent()
                    appos += ('modified', word.getToken())
                    modifiedAppos.append(word.getToken())
                else:
                    word = apposDep.getHead()
                    appos += ('modifier', word.getToken())
                    modifierAppos.append(word.getToken())
                    
        return appos, modifiedAppos, modifierAppos
    
    def getModal(self, verb, allDepDict):
        if verb == '':
            return []
        if 'aux' in allDepDict:
            for auxDep in allDepDict['aux']:
                if auxDep.isHead(verb.getIndex()):
                    auxWord = auxDep.getDependent()
                    auxTag = self.getTagFromIndex(auxWord.getIndex())
                    if auxTag.getPOS() == 'MD':
                        return auxWord.getToken()
        return []
        
    def getCondOfN(self, nounIndex, verb, relDepDict, allDepDict):
        if 'mark' in relDepDict:
            for markDep in relDepDict['mark']:
                if markDep.isHead(nounIndex):
                    markWord = markDep.getDependent()
                    markTag = self.getTagFromIndex(markWord.getIndex())
                    if markTag.getPOS() == 'IN':
                        return markWord.getToken()
        if 'mark' in allDepDict:
            for markDep in allDepDict['mark']:
                if markDep.isHead(verb.getIndex()):
                    markWord = markDep.getDependent()
                    markTag = self.getTagFromIndex(markWord.getIndex())
                    if markTag.getPOS() == 'IN':
                        return markWord.getToken()
        return []
    
    def isPluralN(self, nounTag):
        noun = nounTag.getWord().lower()
        lemma = nounTag.getLemma().lower()
        tag = nounTag.getPOS()
        
        if tag in singularTags:
            if noun != lemma:
                return "ambiguous"
            else:
                return "singular"
        if tag in pluralTags:
            if noun != lemma:
                return "plurarl"
            else: 
                return "ambiguous"
    
    def isPluralV(self, verbPOS):
        '''
        Determines whether a verb is concretely plural, concretely singular, or ambiguous (in the past tense)
        and returns the plurality of the verb.    
        '''
        if verbPOS == 'VBP':
            return "plural"
        elif verbPOS == 'VBZ':
            return "singular"
        elif verbPOS == '':
            return ''
        else:
            return "ambiguous"
    
    def getDenumerator(self, determiners, adjectives):
        for determiner in determiners:
            if determiner in unit:
                return determiner, "unit"
            if determiner in typeO:
                return determiner, "other"
            for adjective in adjectives:
                if adjective in fuzzy:
                    return adjective, "fuzzy"
        return "", ""
	
	
    def isBare(self, plurality, conjoined, allDepList, isBareShortCut):
    		 # if our word is not bare, then shortcut out and returned linked
        if self.__detDeps or self.__possessed or self.__possessive or self.__nummod or 	self.__denumerator:
            return 'linked'
        
        # if the word is not singular or plural
        if plurality not in ['singular','plural']:
            return 'linked'

        
        if conjoined and not isBareShortCut: # our noun is head of conjunction so we do not check the conjoined for bareness
            conjIndex = conjoined[0].getIndex() # Should only ever be one? (a previous assumption)
            conjRelDep = NounAnalysis.generateRelevantDependencies(allDepList, conjIndex)
            conjRelDepDict = NounAnalysis.getRelevantDependenciesAsDict(conjRelDep)
        		# if the conjunct has a determiner it is not bare
            conjDet = self.getDet(conjIndex, conjRelDepDict)
            if conjDet:
                return 'linked'
			
            conjPossd = []
            conjPossv = []
            if 'nmod' in conjRelDepDict:
                for conjPossDep in conjRelDepDict['nmod']:
                    if conjPossDep.getSubType() == 'poss':
                        if conjPossDep.isHead(conjIndex):
                            conjPossv.append(conjPossDep.getDependent().getToken())
                        else:
                            conjPossd.append(conjPossDep.getHead().getToken())
					# if the conjunct is possessed or posssessive return linked
            if conjPossd or conjPossv:
                return 'linked'
            # if the conjunct is nummerically modified return linked
            conjNummod = self.getNummod(conjIndex, conjRelDepDict)
            if conjNummod:
                return 'linked'
            # retrieve adjectives to check conjunct for determiner
            # if the conjunct has a denumerator then return linked
            conjAdj = self.getAdjs(conjIndex, conjRelDepDict)
            conjDen = self.getDenumerator(conjDet, conjAdj)
            if conjDen:
                return 'linked'
        
        return 'bare ' + str(plurality)			

    # returns the Tag object using the word's parsed index (which is 1 based)
    def getTagFromIndex(self, index):
        return self.__sentence.getTags()[index - 1] # switch to zero based
    
    def getDeterminerType(det):
        determiner = det.lower()
        if determiner in indef_articles:
            detType ='indefinite article'
        elif determiner in def_articles:
            detType ='definite article'
        elif determiner in demonstratives:
            detType ='demonstrative'
        elif determiner in quantifiers:
            detType ='quantifier'
        else:
            detType ='other'
        return detType

    # dependencies should be a list of dependency objects, wordIndex is the 
    # word to retrieve relevant dependencies for
    def generateRelevantDependencies(dependencies, wordIndex):
        relDep = []
        
        for dep in dependencies:
            if dep.hasIndex(wordIndex):
                relDep.append(dep)
        return relDep
		
    # Stores the relevant dependencies in a dictionary to enable constant time
    # lookup to lists of dependencies using the type as the key
    def getRelevantDependenciesAsDict(dependencies):
        dependenciesDict = {}
        for dep in dependencies:
            key = dep.getDependencyRelationship()
            if key in dependenciesDict:
                dependenciesDict[key].append(dep)
            else:
                dependenciesDict[key] = [dep]
        return dependenciesDict
    
    # TODO consider where/whether to define the 'fragment' of sentence
    def getSentence(self):
        return self.__sentence
    
    def getNoun(self):
        return self.__noun
    def getNounIndex(self):
        return self.__nounIndex
    def getRelevantDependencies(self):
        return self.__relevantDependencies
    
    def getAllDependencies(self):
        return self.__sentence.getDependencies()
    def getAllTags(self):
        return self.getSentence().getTags()
    def getSentFrag(self):
        '''Returns the context of the given noun.
        
        Parameters
        ----------
        string(sent): the given sentence
        int(index)
        
        Returns
        -------
        string(sentfrag)
        '''
        sent = self.getSentence().getSentence()
        index = self.getNounIndex()
        arr = sent.split()
        if (index-6) < 0:
            startindex = 0
        else:
            startindex = index-6
        if (index+5) > len(arr):
            endindex = len(arr)
        else:
            endindex = index+5
        sentfragarr = arr[startindex:endindex]
        sentfrag = ' '.join(sentfragarr)
        return sentfrag

    def getCorefs(self, sentID, corefs):
        # Coref output format:
        # [length of chain, is_head, is_corrupted, absolute location in chain, relative location in chain, distance from previous mention]
        result_temp = []
        result_temp.append(len(corefs))
        counter_temp = 0
        sent_prev_temp = 0
        #is_head = 
        for ent in corefs:
            counter_temp = counter_temp + 1
            if ent[6] == sentID:
                result_temp.append(ent[3])
                result_temp.append(ent[7]) # is_corrupted
                result_temp.append(counter_temp)
                result_temp.append(counter_temp/len(corefs))
                if ent[3]:
                    result_temp.append(0)
                else:
                    result_temp.append(int(ent[6]) - sent_prev_temp)
                break
            sent_prev_temp = int(ent[6])
        return result_temp
    
    def getAllFeatures(self):
        row = []
        row.append(self.getSentence().getSentence())
        row.append(self.getAllTags())
        row.append(self.getAllDependencies())
        row.append(self.getNoun())
        row.append(self.getNounIndex())
        row.append(self.getRelevantDependencies())
        row.append(self.getSentFrag())
        row.append(self.__nounPOS)
        row.append(self.__negDeps)
        row.append(self.__verb)
        row.append(self.__verbLemma)
        row.append(self.__verbPOS)
        row.append(self.__relationToVerb)
        row.append(self.__verbAdvMod)
        row.append(self.__verbNeg)
        row.append(self.__aux)
        row.append(self.__copOtherPOS)        
        row.append(self.__prepPhrases)        
        row.append(self.__prepositions)        
        row.append(self.__prepSubjects)        
        row.append(self.__prepObjects)        
        row.append(self.__detDeps)
        row.append(self.__detType)
        row.append(self.__conjunctionPhrases)
        row.append(self.__conjunctions)
        row.append(self.__conjoined)
        row.append(self.__compoundHead)
        row.append(self.__compoundMod)
        row.append(self.__adjs)
        row.append(self.__adjbehav)
        row.append(self.__adjbody)
        row.append(self.__adjfeel)
        row.append(self.__adjmind)
        row.append(self.__adjmisc)
        row.append(self.__adjmotion)
        row.append(self.__adjpercep)
        row.append(self.__adjquant)
        row.append(self.__adjsocial)
        row.append(self.__adjspatial)
        row.append(self.__adjsubst)
        row.append(self.__adjtemp)
        row.append(self.__adjweather)
        row.append(self.__possessed)
        row.append(self.__possessive)
        row.append(self.__nummod)
        row.append(self.__case)
        row.append(self.__adv)
        row.append(self.__appos)
        row.append(self.__modifierAppos)
        row.append(self.__modifiedAppos)
        row.append(self.__modal)
        row.append(self.__cond)
        row.append(self.__denumerator)
        row.append(self.__denType)
        row.append(self.__pluN)
        row.append(self.__bare)
        row.append(self.__pluV)
        #row.append(self.__coref)
        row.append(self.__lenOfChain)
        row.append(self.__isHead)
        row.append(self.__isCorrupted)
        row.append(self.__absLocInChain)
        row.append(self.__relLocInChain)
        row.append(self.__distFromPrevMen)
        return row
    
    def testPrint(nounAnalyses):
        print(type(nounAnalyses))
        for a in nounAnalyses:
            '''for dep in a.getSentence().getDependencies():
                print(dep)
            for tag in a.getSentence().getTags():
                print(tag)'''
            print("noun",a.__noun)
            print("nounPOS", a.__nounPOS)
            print('relDep')
            for dep in a.__relevantDependencies:
                print("\t",dep)
            print('negDeps',a.__negDeps)
            print('verb',a.__verb)
            print('relationToVerb',a.__relationToVerb)
            print('verbPOS',a.__verbPOS)
            print('verbLemma',a.__verbLemma)
            print('aux',a.__aux)
            print('copOtherPOS',a.__copOtherPOS)
            print('detType', a.__detType)
            print('detDeps',a.__detDeps)
            print('conjoined,',a.__conjoined)
            print('------------------------------------------------------------------')

    def generateNounAnalyses(rawSentence):
        nounAnalyses = []
        nounIndex = 1
        for tag in rawSentence.getTags():
            if tag.isNoun() and tag.getLemma() in celexDict:
                nounAnalyses.append(NounAnalysis(rawSentence, tag, nounIndex))
            nounIndex += 1
        
        return nounAnalyses
    
        #for noun in nouns:

# TODO Static initialization? 
indef_articles = ['a','an','some']
def_articles = ['the']
demonstratives = ['this','that','those','these','which']
quantifiers = ['each','every','few','a few','many','much','some','any','all']
adj_list=['BEHAVIOR', 'BODY', 'FEELING', 'MIND', 'MISCELLANEOUS', 'MOTION', 'PERCEPTION', 'QUANTITY', 'SOCIAL', 'SPATIAL', 'SUBSTANCE', 'TEMPORAL', 'WEATHER']
unit = ['a', 'an', 'one', '1'] #fall under determiners or numbers
fuzzy = ['several', 'many', 'few'] #fall under adjectives, excludes fuzzy numbers
typeO = ['each', 'every','either', 'both'] #fall under determiners, excludes concrete numbers
verbPOSs = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']
singularTags = ['NN', 'NNP']
pluralTags = ['NNS', 'NNPS']
def getAdjType(adj):
    global adjdict
    if not adjdict:
        loadAdjTypes()
    adjtype = []
    for i in adj:
        if i in adjdict:
            adjtype.append(adjdict[i])
    vec = [x for x in zip(*adjtype)]
    return vec

def loadAdjTypes(): 
    '''
    This converts the data in words.predicted to a Python dictionary (adjdict).
    '''
    global adjdict
    adjdict = {}
    adjdf = open(file_directory+"/words.predicted", 'r')
    for ln in adjdf:
        l = re.findall(r"(.*)({.*})", ln)
        word = l[0][0].split("\t")[0]
        word_dict=ast.literal_eval(l[0][1])
        # print word_dict
        vec=[]
        for adj_type in adj_list:
            vec.append(word_dict[adj_type])
        # print vec
        adjdict[word] = vec
    return adjdict

# Sample test code, adjdict = loadAdjTypes() only need be run once.
file_directory = 'C:/Users/Samson/Downloads'
'''
line= ["Section : Life and Letters  I do n't remember hearing the phrase '' white guilt '' very much before the mid-1960s .",
 "Section/section/NN :/:/: Life/Life/NNP and/and/CC Letters/letter/NNS I/I/PRP do/do/VBP n't/not/RB remember/remember/VB hearing/hear/VBG the/the/DT phrase/phrase/NN ''/''/'' white/white/JJ guilt/guilt/NN ''/''/'' very/very/RB much/much/RB before/before/IN the/the/DT mid-1960s/mid-1960/NNS ././.",
 "ROOT (ROOT-0, Section-1)punct (Section-1, :-2) dep (Section-1, Life-3) cc (Life-3, and-4) dep (Section-1, Letters-5) conj:and (Life-3, Letters-5) nsubj (remember-9, I-6) aux (remember-9, do-7) neg (remember-9, n't-8) acl:relcl (Letters-5, remember-9) xcomp (remember-9, hearing-10) det (guilt-15, the-11) compound (guilt-15, phrase-12) punct (guilt-15, ''-13) amod (guilt-15, white-14) dobj (hearing-10, guilt-15) punct (hearing-10, ''-16) advmod (much-18, very-17) advmod (mid-1960s-21, much-18) case (mid-1960s-21, before-19) det (mid-1960s-21, the-20) nmod:before (hearing-10, mid-1960s-21) punct (Section-1, .-22) ",
 '',
 '1',
 '4000161',
 '[["I",\'I\',\'I\',True,6,7,1,False],["I",\'I\',\'I\',False,8,9,2,False],["I",\'I\',\'I\',False,2,3,3,False],["me",\'me\',\'I\',False,20,21,3,False],["me",\'me\',\'I\',False,32,33,3,False],["I",\'I\',\'I\',False,1,2,4,False],["I",\'I\',\'I\',False,13,14,4,False],["myself",\'myself\',\'myself\',False,15,16,5,False],["I",\'I\',\'I\',False,1,2,6,False],["I",\'I\',\'I\',False,14,15,6,False],["me",\'me\',\'I\',False,8,9,7,False],["my",\'my\',\'my\',False,8,9,8,False],["my",\'my\',\'my\',False,42,43,8,False],["me",\'me\',\'I\',False,25,26,9,False],["my",\'my\',\'my\',False,27,28,9,False],["I",\'I\',\'I\',False,1,2,10,False],["my",\'my\',\'my\',False,18,19,10,False],["I",\'I\',\'I\',False,2,3,11,False],["I",\'I\',\'I\',False,17,18,11,False],["my",\'my\',\'my\',False,9,10,15,False],["I",\'I\',\'I\',False,12,13,20,False],["I",\'I\',\'I\',False,1,2,21,False]]']
#adjdict = loadAdjTypes()
#raw = Raw(line)
#nounAnalyses = NounAnalysis.generateNounAnalyses(raw)
#print(nounAnalyses[0].getAllFeatures())

celexDict = {}
line = []
output_dir = file_directory + '/test/'
with open(output_dir +'esl.txt','r') as f:
    raw = csv.reader(f,delimiter='\\')
    for row in raw:
        if row[3] == '1':
            celexDict[row[1].lower()] = row[4:9] 
with open(file_directory + '/head_acad_1990.csv', 'r') as raw_file:
    import time

    t0 = time.clock()
    raw_reader = csv.reader(raw_file)
    next(raw_reader)
    for row in raw_reader:
        line = row
        raw = Raw(row)
        
        for analysis in NounAnalysis.generateNounAnalyses(raw):
            output_file = output_dir + analysis.getNoun() + 'Out.csv'
            if not os.path.isfile(output_file):
                with open(output_file, 'w') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Sentence','Tags','Dependencies','Noun','Index','Relevant Dependencies','Sentence Fragment','Noun Tag','Negation','Verb','Verb Lemma','Verb Tag','Relation to Verb','Verb Adverbial Modifier','Verb Negation','Auxillary','Copula Other Tag', 'Prepositional Phrases', 'Prepositions','Prepositional Subjects','Prepositional Objects','Determiners','Determiner Type','Conjunction Phrases',	'Conjunctions',	'Conjoined', 'Compound Head', 'Compound Modifiers','Adjectival Modifiers',	'AdjType: Behavior',	'AdjType: Body',	'AdjType: Feeling',	'AdjType: Mind',	'AdjType: Miscellaneous',	'AdjType: Motion',	'AdjType: Perception',	'AdjType: Quantity',	'AdjType: Social',	'AdjType: Spatial',	'AdjType: Substance',	'AdjType: Temporal',	'AdjType: Weather', 'Possesed owned by noun','Possesive owner of noun','Numeric Modifiers','Case Modifiers','Adverbial Modifiers','Appositionals','Appositional Modifiers','Modified Appositives','Modality','Conditional','Denumerator','Type of Denumerator','Plurality of Noun','Bareness of Noun','Plurality of Verb','length of chain', 'is_head, is_corrupted', 'absolute location in chain', 'relative location in chain', 'distance from previous mention'])
                    writer.writerow(analysis.getAllFeatures())
            else:
                with open(output_file, 'a') as f:
                    writer = csv.writer(f)
                    writer.writerow(analysis.getAllFeatures())
    t1 = time.clock()
    print(t1-t0)
'''