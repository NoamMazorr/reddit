from nltk.corpus import wordnet as wn, stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import word_tokenize
import sys, yake


class keywords:
    @staticmethod
    def get_similarity(word1, word2):
        '''
        get simularity of two words. returns score from 0.1 to 1.0
        '''
        try:
            if word1 == word2:
                return 1.0
            
            w1 = wn.synset(f'{word1}.n.01')
            w2 = wn.synset(f'{word2}.n.01')
            # calculate similarity
            return w1.wup_similarity(w2)

        except Exception as e:
            # try to get similarity of synonyms of a word that is not included in wordnet
            exc_type, exc_obj, exc_tb = sys.exc_info()
            line_num = exc_tb.tb_lineno
            if line_num == 17:
                word = word1
                ok_word = word2
            else:
                word = word2
                ok_word = word1

            synonyms = []
            for syn in wn.synsets(word):
               for lm in syn.lemmas():
                       synonyms.append(lm.name())

            comperisons = []
            for syn in synonyms:
                try:
                    w1 = wn.synset(f'{syn}.n.01')
                    w2 = wn.synset(f'{ok_word}.n.01')
                    comperisons.append(w1.wup_similarity(w2))
                except:
                    pass

            if comperisons:
                return max(comperisons)
            else:
                return 0.1

    @staticmethod
    def get_keywords_with_scores(text, max_ngram_size, duplication_threshold):
        '''
        extract keywords from text
        '''
        kw_extractor = yake.KeywordExtractor(n=max_ngram_size, dedupLim=duplication_threshold, top=100)
        keywords = kw_extractor.extract_keywords(text)

        # stem keywords
        ps = PorterStemmer()
        for i, word in enumerate(keywords):
            keywords[i] = list(keywords[i])
            keywords[i][0] = ps.stem(word[0])

        # remove duplicate
        new_keywords = []
        for word in keywords:
            if word not in new_keywords:
                new_keywords.append(word)
        keywords = new_keywords

        return keywords

    @staticmethod
    def stem_keyword(word):
        '''
        get base form of a word.
        '''
        ps = PorterStemmer()
        return ps.stem(word)

    @staticmethod
    def match_keywords(keywords, word):
        '''
        returns matches between word input and keywords
        '''
        # creat PorterStemmer object for stemming and get set of stopwords
        ps = PorterStemmer()
        stop_words = set(stopwords.words('english'))

        tokenized_word = word_tokenize(word)

        # remove stopwords and stem words
        tokenized_word = [ps.stem(w) for w in tokenized_word if not w.lower() in stop_words]

        result = []
        for keyword in keywords:
            # tokenize, stem and remove stopwords each keyword
            tokenized_keyword = [ps.stem(w) for w in word_tokenize(keyword['word']) if not w.lower() in stop_words]
            
            # add keyword details if a shared word is found between tokenized_keyword and tokenized_word
            if set(tokenized_keyword).intersection(set(tokenized_word)):
                result.append((keyword['score'], keyword['word'], keyword['subr_id']))

        return result
