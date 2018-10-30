
import edu.stanford.nlp.coref.data.CorefChain;
import edu.stanford.nlp.coref.data.CorefChain.CorefMention;
import java.util.List;
import java.util.Objects;

public class Chain implements Comparable<Chain>{
    private int currentSentenceNum;
    private final List<CorefMention> corefMentions;
    private int index = 0;
    private boolean[] corruptSentences;
    
    public Chain(CorefChain corefChain){
        corefMentions = corefChain.getMentionsInTextualOrder();
        corruptSentences = new boolean[corefMentions.size()];
        currentSentenceNum = corefMentions.get(index).sentNum;
    }
    
    public boolean increment(boolean corrupt){
        for (; index < corefMentions.size(); index++) {
            int prev = currentSentenceNum;
            corruptSentences[index] = corrupt;
            currentSentenceNum = corefMentions.get(index).sentNum;
            if(prev != currentSentenceNum)
                break;
        }
        // returns true if chain is complete
        return index == corefMentions.size();
    }
    
    public int getCurrentSentenceNum() {
        return currentSentenceNum;
    }
    public List<CorefMention> getCorefMentions() {
        return corefMentions;
    }
    
    public boolean isCorrupt(int index){
        return corruptSentences[index];
    }
    @Override
    public int compareTo(Chain o) {
        return Integer.compare(currentSentenceNum, o.currentSentenceNum);
    }

    @Override
    public int hashCode() {
        int hash = 7;
        hash = 17 * hash + Objects.hashCode(this.corefMentions);
        return hash;
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }
        if (obj == null) {
            return false;
        }
        if (getClass() != obj.getClass()) {
            return false;
        }
        final Chain other = (Chain) obj;
        if (!Objects.equals(this.corefMentions, other.corefMentions)) {
            return false;
        }
        return true;
    }

    
    
    @Override
    public String toString() {
        return "Chain{" + "currentSentenceNum=" + currentSentenceNum + ", corefMentions=" + corefMentions + ", index=" + index + '}';
    }
}