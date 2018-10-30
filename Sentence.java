/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
//package csc450project3;

import edu.stanford.nlp.coref.data.CorefChain;
import edu.stanford.nlp.coref.data.CorefChain.CorefMention;
import edu.stanford.nlp.ling.CoreLabel;
import edu.stanford.nlp.ling.IndexedWord;
import edu.stanford.nlp.pipeline.CoreSentence;
import edu.stanford.nlp.semgraph.SemanticGraph;
import edu.stanford.nlp.semgraph.SemanticGraphEdge;

import java.util.LinkedList;
import java.util.List;


public class Sentence {
    CoreSentence mCoreSent;
    private int mSentenceID;
    private String mPassageID;
    LinkedList<Chain> mChainList;

    public Sentence(CoreSentence corefSent, int sId, String pId){
        mCoreSent = corefSent;
        mSentenceID = sId;
        mPassageID = pId;
        mChainList = new LinkedList<>();
    }

    public void addChain(Chain chain){
        mChainList.add(chain);
    }

    public CoreSentence getCorefSent(){
        return mCoreSent;
    }

    public LinkedList<Chain> getChains(){
        return mChainList;
    }

    @Override
    public String toString(){
        StringBuilder builder = new StringBuilder();
        builder.append("\"").append(mCoreSent.text().replaceAll("\"", "''")).append("\",");
        // tags
        builder.append("\"");
        for(int i = 0; i < mCoreSent.tokens().size(); i++){
            builder.append(mCoreSent.tokens().get(i).word().replaceAll("\"", "''")).
                    append("/").append(mCoreSent.tokens().get(i).lemma().replaceAll("\"", "''")).
                    append("/").append(mCoreSent.posTags().get(i).replaceAll("\"", "''"));
            if(i != mCoreSent.tokens().size() - 1){
                builder.append(" ");
            }
        }
        builder.append("\",");

        // parse
        SemanticGraph dep = mCoreSent.dependencyParse();
        builder.append("\"");
        builder.append("ROOT (ROOT-0, ");
        builder.append(depWordFormat(dep.getFirstRoot()).replaceAll("\"", "''")) ;
        builder.append(")");
        List<SemanticGraphEdge> edgeList = dep.edgeListSorted();
        for(SemanticGraphEdge edge : edgeList){
            builder.append(edge.getRelation()) ;
            builder.append(" (") ;
            builder.append(depWordFormat(edge.getGovernor()).replaceAll("\"", "''"));
            builder.append(", ") ;
            builder.append(depWordFormat(edge.getDependent()).replaceAll("\"", "''")) ;
            builder.append(") ");
        }
        builder.append("\",");

        // ner
        builder.append("\"");
        for(int i = 0; i < mCoreSent.tokens().size(); i++){
            if(!mCoreSent.tokens().get(i).ner().equals("O")){
                builder.append(mCoreSent.tokens().get(i).word().replaceAll("\"", "''"));
                builder.append("/");
                builder.append(i);
                builder.append("/");
                builder.append(mCoreSent.tokens().get(i).ner().replaceAll("\"", "''"));
                if(i != mCoreSent.tokens().size() - 1){
                    builder.append(" ");
                }
            }
        }
        builder.append("\",");

        // Sentence and paragraph number
        builder.append(mSentenceID);
        builder.append(",");
        builder.append(mPassageID);
        
        for(Chain cc : mChainList){
                List<CorefMention> mentions = cc.getCorefMentions();
                Boolean first = true;
                builder.append(",\"[");
                for (int i = 0; i < mentions.size(); i++){
                    CorefChain.CorefMention cm = mentions.get(i);
                    CoreLabel headWord = mCoreSent.document().sentences().get(cm.sentNum - 1).tokens().get(cm.headIndex - 1);
                    builder.append("[\"\"").append(cm.mentionSpan).append("\"\",").append("'").
                            append(headWord.word()).append("','").
                            append(headWord.lemma()).append("',").
                            append(first ? "True" : "False").append(",").
                            append(cm.startIndex).append(",").
                            append(cm.endIndex).append(",").
                            append(cm.sentNum).append(",").
                            append(cc.isCorrupt(i) ? "True" : "False").
                            append("]");
                    if(i < mentions.size() - 1)
                        builder.append(",");
                    first = false;
                }
                builder.append("]\"");
        }
        return builder.toString();
    }

    private String depWordFormat(IndexedWord word){
        return word.originalText()+"-"+word.index();
    }
}