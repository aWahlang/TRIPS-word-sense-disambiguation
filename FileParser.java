import edu.stanford.nlp.coref.CorefCoreAnnotations;
import edu.stanford.nlp.coref.data.CorefChain;
import edu.stanford.nlp.ling.IndexedWord;
import edu.stanford.nlp.pipeline.CoreDocument;
import edu.stanford.nlp.pipeline.CoreSentence;
import edu.stanford.nlp.pipeline.StanfordCoreNLP;

import java.io.*;
import java.util.Collection;
import java.util.PriorityQueue;
import javax.swing.JFileChooser;

public class FileParser implements Parser{

    private StanfordCoreNLP mPipeline;

    public FileParser(StanfordCoreNLP pipeline){
        mPipeline = pipeline;
    }

    @Override
    public boolean parse(File file) {;
        String buffer = null;
        System.out.println(file.getAbsolutePath());
        try (BufferedReader bufferedReader = new BufferedReader(new FileReader(file));
            BufferedWriter bufferedWriter = new BufferedWriter(new FileWriter(prepareOutput(file), false));){
            String id;
            bufferedWriter.write("\"sent\",\"tags\",\"parse\",\"ner\",\"open IE\",\"open IE index\",\"sentence number\",\"paragraph number\",\"CorefChain\"");
            bufferedWriter.newLine();
            bufferedWriter.flush();
            while ((buffer = bufferedReader.readLine()) != null){
                while(buffer != null && buffer.isEmpty()){
                    buffer = bufferedReader.readLine();
                }
                if(buffer == null){
                    return false;
                }
                id = buffer.substring(2,9);
                buffer = buffer.substring(10);
                buffer = buffer.replaceAll("<p>","");
                CoreDocument document = new CoreDocument(buffer);
                mPipeline.annotate(document);
                PriorityQueue<Chain> queue = new PriorityQueue<>();
                
                Collection<CorefChain> corefChain = document.annotation().get(CorefCoreAnnotations.CorefChainAnnotation.class).values();
                for(CorefChain cc : corefChain)
                    queue.add(new Chain(cc));
                int sentenceNum = 0;
                for(CoreSentence sentence : document.sentences()){
                    sentenceNum++;
                    boolean corrupt = sentence.text().contains("@ @");
                    handleSentence(sentence, sentenceNum, id, queue, corrupt, bufferedWriter); 
                }

                System.out.println("Finished parsing ##"+id);
                break;
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
            return false;
        } catch (IOException e) {
            e.printStackTrace();
        } catch (IndexOutOfBoundsException e){
            e.printStackTrace();
            System.err.print(buffer);
        }
        return false;
    }

    private void handleSentence(CoreSentence sentence, int sentenceNum, String id, PriorityQueue<Chain> queue, boolean corrupt, final BufferedWriter bufferedWriter) throws IOException {
        if(corrupt){ // Stuff that needs to happen regardless of corruption
            while(queue.peek() != null && sentenceNum == queue.peek().getCurrentSentenceNum()){
                Chain chainToAdd = queue.poll();
                boolean endOfChain = chainToAdd.increment(corrupt);
                if(!endOfChain){
                    queue.add(chainToAdd);
                }
            }
        } else {
            Sentence sent = new Sentence(sentence, sentenceNum, id); 
            while(queue.peek() != null && sentenceNum == queue.peek().getCurrentSentenceNum()){
                Chain chainToAdd = queue.poll();
                sent.addChain(chainToAdd);
                boolean endOfChain = chainToAdd.increment(corrupt);

                if(!endOfChain){
                    queue.add(chainToAdd);
                }
            }
            bufferedWriter.write(sent.toString());
            bufferedWriter.newLine();
            bufferedWriter.flush();
        }
    }

    private String depWordFormat(IndexedWord word){
        return word.originalText()+"-"+word.index();
    }
    private File prepareOutput(File input){
        String temp = input.getAbsolutePath();
        return new File(temp.substring(0,temp.length() - 4) + ".csv");
    }

    private File prepareCorefOutput(File input){
        String temp = input.getAbsolutePath();
        return new File(temp.substring(0,temp.length() - 4) + "_coref.csv");
    }
    
    public static void main(String[] args){
        
        JFileChooser jfc = new JFileChooser();
        int selection = jfc.showOpenDialog(jfc);
        if(selection == JFileChooser.APPROVE_OPTION){
            File file = jfc.getSelectedFile();
            CorpusParser fp = new CorpusParser();
            fp.parse(file);
        }
    }
}
