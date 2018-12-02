import os
import string
from robot.api.deco import keyword
from robot.api import logger
import time
import datetime
import csv

class Find_And_Replace(object):

    def __init__(self, case_sensitive=False):
        self._keyword = '_keyword_'
        self._white_space_chars = set(['.', '\t', '\n', '\a', ' ', ','])
        self.non_word_boundaries = set(string.digits + string.ascii_letters + '_')
        self.keyword_trie_dict = dict()
        self.case_sensitive = case_sensitive
        self._terms_in_trie = 0
        self.ROBOT_SUPPRESS_NAME = True

    def __len__(self):
        return self._terms_in_trie

    def __contains__(self, word):
        if not self.case_sensitive:
            word = word.lower()
        current_dict = self.keyword_trie_dict
        len_covered = 0
        for char in word:
            if char in current_dict:
                current_dict = current_dict[char]
                len_covered += 1
            else:
                break
        return self._keyword in current_dict and len_covered == len(word)

    def __getitem__(self, word):
        if not self.case_sensitive:
            word = word.lower()
        current_dict = self.keyword_trie_dict
        len_covered = 0
        for char in word:
            if char in current_dict:
                current_dict = current_dict[char]
                len_covered += 1
            else:
                break
        if self._keyword in current_dict and len_covered == len(word):
            return current_dict[self._keyword]

    def __setitem__(self, keyword, clean_name=None):

        status = False
        if not clean_name and keyword:
            clean_name = keyword

        if keyword and clean_name:
            if not self.case_sensitive:
                keyword = keyword.lower()
            current_dict = self.keyword_trie_dict
            for letter in keyword:
                current_dict = current_dict.setdefault(letter, {})
            if self._keyword not in current_dict:
                status = True
                self._terms_in_trie += 1
            current_dict[self._keyword] = clean_name
        return status

    def __delitem__(self, keyword):

        status = False
        if keyword:
            if not self.case_sensitive:
                keyword = keyword.lower()
            current_dict = self.keyword_trie_dict
            character_trie_list = []
            for letter in keyword:
                if letter in current_dict:
                    character_trie_list.append((letter, current_dict))
                    current_dict = current_dict[letter]
                else:
                    # if character is not found, break out of the loop
                    current_dict = None
                    break
            # remove the characters from trie dict if there are no other keywords with them
            if current_dict and self._keyword in current_dict:
                # we found a complete match for input keyword.
                character_trie_list.append((self._keyword, current_dict))
                character_trie_list.reverse()

                for key_to_remove, dict_pointer in character_trie_list:
                    if len(dict_pointer.keys()) == 1:
                        dict_pointer.pop(key_to_remove)
                    else:
                        # more than one key means more than 1 path.
                        # Delete not required path and keep the other
                        dict_pointer.pop(key_to_remove)
                        break
                # successfully removed keyword
                status = True
                self._terms_in_trie -= 1
        return status

    def __iter__(self):

        raise NotImplementedError("Please use get_all_keywords() instead")

    def __set_non_word_boundaries(self, non_word_boundaries):
        self.non_word_boundaries = non_word_boundaries

    def __add_non_word_boundary(self, character):
        self.non_word_boundaries.add(character)

    def __add_keyword(self, keyword, clean_name=None):

        return self.__setitem__(keyword, clean_name)

    def __remove_keyword(self, keyword):
        return self.__delitem__(keyword)

    def __get_keyword(self, word):
        return self.__getitem__(word)

    def __remove_keywords_from_list(self, keyword_list):
        if not isinstance(keyword_list, list):
            raise AttributeError("keyword_list should be a list")

        for keyword in keyword_list:
            self.__remove_keyword(keyword)

    def __get_all_keywords(self, term_so_far='', current_dict=None):

        terms_present = {}
        if not term_so_far:
            term_so_far = ''
        if current_dict is None:
            current_dict = self.keyword_trie_dict
        for key in current_dict:
            if key == '_keyword_':
                terms_present[term_so_far] = current_dict[key]
            else:
                sub_values = self.__get_all_keywords(term_so_far + key, current_dict[key])
                for key in sub_values:
                    terms_present[key] = sub_values[key]
        return terms_present

    def __extract_keywords(self, sentence, span_info=False):
        keywords_extracted = []
        if not sentence:
            # if sentence is empty or none just return empty list
            return keywords_extracted
        if not self.case_sensitive:
            sentence = sentence.lower()
        current_dict = self.keyword_trie_dict
        sequence_start_pos = 0
        sequence_end_pos = 0
        reset_current_dict = False
        idx = 0
        sentence_len = len(sentence)
        while idx < sentence_len:
            char = sentence[idx]
            # when we reach a character that might denote word end
            if char not in self.non_word_boundaries:

                # if end is present in current_dict
                if self._keyword in current_dict or char in current_dict:
                    # update longest sequence found
                    sequence_found = None
                    longest_sequence_found = None
                    is_longer_seq_found = False
                    if self._keyword in current_dict:
                        sequence_found = current_dict[self._keyword]
                        longest_sequence_found = current_dict[self._keyword]
                        sequence_end_pos = idx

                    # re look for longest_sequence from this position
                    if char in current_dict:
                        current_dict_continued = current_dict[char]

                        idy = idx + 1
                        while idy < sentence_len:
                            inner_char = sentence[idy]
                            if inner_char not in self.non_word_boundaries and self._keyword in current_dict_continued:
                                # update longest sequence found
                                longest_sequence_found = current_dict_continued[self._keyword]
                                sequence_end_pos = idy
                                is_longer_seq_found = True
                            if inner_char in current_dict_continued:
                                current_dict_continued = current_dict_continued[inner_char]
                            else:
                                break
                            idy += 1
                        else:
                            # end of sentence reached.
                            if self._keyword in current_dict_continued:
                                # update longest sequence found
                                longest_sequence_found = current_dict_continued[self._keyword]
                                sequence_end_pos = idy
                                is_longer_seq_found = True
                        if is_longer_seq_found:
                            idx = sequence_end_pos
                    current_dict = self.keyword_trie_dict
                    if longest_sequence_found:
                        keywords_extracted.append((longest_sequence_found, sequence_start_pos, idx))
                    reset_current_dict = True
                else:
                    # we reset current_dict
                    current_dict = self.keyword_trie_dict
                    reset_current_dict = True
            elif char in current_dict:
                # we can continue from this char
                current_dict = current_dict[char]
            else:
                # we reset current_dict
                current_dict = self.keyword_trie_dict
                reset_current_dict = True
                # skip to end of word
                idy = idx + 1
                while idy < sentence_len:
                    char = sentence[idy]
                    if char not in self.non_word_boundaries:
                        break
                    idy += 1
                idx = idy
            # if we are end of sentence and have a sequence discovered
            if idx + 1 >= sentence_len:
                if self._keyword in current_dict:
                    sequence_found = current_dict[self._keyword]
                    keywords_extracted.append((sequence_found, sequence_start_pos, sentence_len))
            idx += 1
            if reset_current_dict:
                reset_current_dict = False
                sequence_start_pos = idx
        if span_info:
            return keywords_extracted
        return [value[0] for value in keywords_extracted]

    def __replace_keywords(self, sentence):
        if not sentence:
            # if sentence is empty or none just return the same.
            return sentence
        new_sentence = []
        orig_sentence = sentence
        if not self.case_sensitive:
            sentence = sentence.lower()
        current_word = ''
        current_dict = self.keyword_trie_dict
        current_white_space = ''
        sequence_end_pos = 0
        idx = 0
        sentence_len = len(sentence)
        while idx < sentence_len:
            char = sentence[idx]
            current_word += orig_sentence[idx]
            # when we reach whitespace
            if char not in self.non_word_boundaries:
                current_white_space = char
                # if end is present in current_dict
                if self._keyword in current_dict or char in current_dict:
                    # update longest sequence found
                    sequence_found = None
                    longest_sequence_found = None
                    is_longer_seq_found = False
                    if self._keyword in current_dict:
                        sequence_found = current_dict[self._keyword]
                        longest_sequence_found = current_dict[self._keyword]
                        sequence_end_pos = idx

                    # re look for longest_sequence from this position
                    if char in current_dict:
                        current_dict_continued = current_dict[char]
                        current_word_continued = current_word
                        idy = idx + 1
                        while idy < sentence_len:
                            inner_char = sentence[idy]
                            current_word_continued += orig_sentence[idy]
                            if inner_char not in self.non_word_boundaries and self._keyword in current_dict_continued:
                                # update longest sequence found
                                current_white_space = inner_char
                                longest_sequence_found = current_dict_continued[self._keyword]
                                sequence_end_pos = idy
                                is_longer_seq_found = True
                            if inner_char in current_dict_continued:
                                current_dict_continued = current_dict_continued[inner_char]
                            else:
                                break
                            idy += 1
                        else:
                            # end of sentence reached.
                            if self._keyword in current_dict_continued:
                                # update longest sequence found
                                current_white_space = ''
                                longest_sequence_found = current_dict_continued[self._keyword]
                                sequence_end_pos = idy
                                is_longer_seq_found = True
                        if is_longer_seq_found:
                            idx = sequence_end_pos
                            current_word = current_word_continued
                    current_dict = self.keyword_trie_dict
                    if longest_sequence_found:
                        new_sentence.append(longest_sequence_found + current_white_space)
                        current_word = ''
                        current_white_space = ''
                    else:
                        new_sentence.append(current_word)
                        current_word = ''
                        current_white_space = ''
                else:
                    # we reset current_dict
                    current_dict = self.keyword_trie_dict
                    new_sentence.append(current_word)
                    current_word = ''
                    current_white_space = ''
            elif char in current_dict:
                # we can continue from this char
                current_dict = current_dict[char]
            else:
                # we reset current_dict
                current_dict = self.keyword_trie_dict
                # skip to end of word
                idy = idx + 1
                while idy < sentence_len:
                    char = sentence[idy]
                    current_word += orig_sentence[idy]
                    if char not in self.non_word_boundaries:
                        break
                    idy += 1
                idx = idy
                new_sentence.append(current_word)
                current_word = ''
                current_white_space = ''
            # if we are end of sentence and have a sequence discovered
            if idx + 1 >= sentence_len:
                if self._keyword in current_dict:
                    sequence_found = current_dict[self._keyword]
                    new_sentence.append(sequence_found)
                else:
                    new_sentence.append(current_word)
            idx += 1
        return "".join(new_sentence)

    @keyword
    def find_and_replace_keyword_from_single_text_file(self, textFile, searchKeyword, replaceKeyword):
        logger.write("Find and Replacing Single Text file started at: " + datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        start_time = time.time()
        if os.path.isfile(textFile):
            txtfile = open(textFile, 'r')
            txtcontent = txtfile.read()
            txtfile.close()
            self.__add_keyword(searchKeyword, replaceKeyword)
            newtxtcontent = self.__replace_keywords(txtcontent)
            txtfile = open(textFile, 'w')
            txtfile.write(newtxtcontent)
            txtfile.close()
            logger.write("Find and Replacing Single Text file stoped at: " + datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            logger.write("Single Text File's Replace Operation took: " + str(time.time() - start_time) + " seconds")
        else:
            logger.error("Not able to find Text file")
            print('*ERROR* Not able to find Text file. ')

    @keyword
    def find_and_replace_keyword_from_multiple_text_file(self, textfilefolder, searchKeyword, replaceKeyword):
        self.__add_keyword(searchKeyword, replaceKeyword)
        logger.write("Find and Replacing Multiple Text file started at: " + datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        start_time = time.time()
        for fle in os.listdir(textfilefolder):
            if fle.endswith('.txt'):
                logger.write("Working With: " + fle)
                txtfile = open(os.path.join(textfilefolder, fle), 'r')
                txtcontent = txtfile.read()
                txtfile.close()
                newtxtcontent = self.__replace_keywords(txtcontent)
                txtfile = open(os.path.join(textfilefolder, fle), 'w')
                txtfile.write(newtxtcontent)
                txtfile.close()
                logger.write("Finished Working With: " + fle)
            else:
                logger.write("No Text files found in folder")
        logger.write("Find and Replacing Multiple Text file stoped at: " + datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logger.write("Multiple Text File's Replace Operation took: " + str(time.time() - start_time) + " seconds")

    @keyword
    def find_and_replace_keyword_from_single_CSV_file(self, textFile, searchKeyword, replaceKeyword):
        logger.write("Find and Replacing Single CSV file started at: " + datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        start_time = time.time()
        if os.path.isfile(textFile):
            txtfile = open(textFile, 'r')
            txtcontent = txtfile.read()
            txtfile.close()
            self.__add_keyword(searchKeyword, replaceKeyword)
            newtxtcontent = self.__replace_keywords(txtcontent)
            txtfile = open(textFile, 'w')
            txtfile.write(newtxtcontent)
            txtfile.close()
            logger.write("Find and Replacing Single Text file stoped at: " + datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            logger.write("Single Text File's Replace Operation took: " + str(time.time() - start_time) + " seconds")
        else:
            logger.error("Not able to find Text file")
            print('*ERROR* Not able to find Text file. ')

    @keyword
    def find_and_replace_keyword_from_multiple_CSV_file(self, textfilefolder, searchKeyword, replaceKeyword):
        self.__add_keyword(searchKeyword, replaceKeyword)
        logger.write("Find and Replacing Multiple Text file started at: " + datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        start_time = time.time()
        for fle in os.listdir(textfilefolder):
            if fle.endswith('.csv'):
                logger.write("Working With: " + fle)
                txtfile = open(os.path.join(textfilefolder, fle), 'r')
                txtcontent = txtfile.read()
                txtfile.close()
                newtxtcontent = self.__replace_keywords(txtcontent)
                txtfile = open(os.path.join(textfilefolder, fle), 'w')
                txtfile.write(newtxtcontent)
                txtfile.close()
                logger.write("Finished Working With: " + fle)
            else:
                logger.write("No Text files found in folder")
        logger.write("Find and Replacing Multiple Text file stoped at: " + datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logger.write("Multiple Text File's Replace Operation took: " + str(time.time() - start_time) + " seconds")



if __name__ == "__main__":
    a = Find_And_Replace()
    # a.find_and_replace_keyword_from_single_text_file('test.txt', 'Lorem', 'Ameya')
    # a.find_and_replace_keyword_from_multiple_text_file('E:\RobotFrameworkProjects\Find-and-Replace\sample_textfiles', 'Lorem', 'Ameya' )
    a.find_and_replace_keyword_from_single_CSV_file('Test_CSV.csv', 'School', 'Ameya')
