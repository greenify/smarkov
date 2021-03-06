#!/usr/bin/env python
# encoding: utf-8
#
# Markov chain manipulation
#
# The MIT License (MIT)
#
# Copyright (c) 2016 greenify
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from collections import defaultdict
from itertools import chain
from . import utils

__author__ = "greenify"
__copyright__ = "Copyright 2016, greenify"


class Markov:
    """ A simple markov chain implementation

        Attributes:
            corpus: given corpus (a corpus_entry needs to be a tuple or array)
            order: maximal order to look back for a given state (default 1)
            tokenize: function how to split an element of the corpus (e.g sentences into words)
    """

    def __init__(self, corpus, order=1, tokenize=lambda x: x):
        """ Initializes the Markov Chain with a given corpus and order """
        assert order >= 1, "Invalid Markov chain order"
        assert order <= 20, "Markov chain order too high"
        assert corpus is not None, "Corpus is empty"
        self.order = order
        self._start_symbol = '^'
        self._end_symbol = '$'
        self.tokenize = tokenize
        self._compute_transitions(corpus, self.order)

    def _compute_transitions(self, corpus, order=1):
        """ Computes the transition probabilities of a corpus
        Args:
            corpus: the given corpus (a corpus_entry needs to be iterable)
            order: the maximal Markov chain order
        """
        self.transitions = defaultdict(lambda: defaultdict(int))

        for corpus_entry in corpus:
            tokens = self.tokenize(corpus_entry)

            last_tokens = utils.prefilled_buffer(
                self._start_symbol, length=self.order)
            # count the occurrences of "present | past"
            for token_value in chain(tokens, self._end_symbol):
                for suffix in utils.get_suffixes(last_tokens):
                    self.transitions[suffix][token_value] += 1

                last_tokens.append(token_value)

        self._compute_relative_probs(self.transitions)

    def _compute_relative_probs(self, prob_dict):
        """ computes the relative probabilities for every state """
        for transition_counts in prob_dict.values():
            summed_occurences = sum(transition_counts.values())
            if summed_occurences > 0:
                for token in transition_counts.keys():
                    transition_counts[token] = transition_counts[
                        token] * 1.0 / summed_occurences

    def _text_generator(self, next_token=None, emit=lambda x, _, __: x, max_length=None):
        """ loops from the start state to the end state and records the emissions
        Tokens are joint to sentences by looking ahead for the next token type

        emit: by default the markovian emit (see HMM for different emission forms)
        max_length: maximum number of emissions
        """
        assert next_token is not None
        last_tokens = utils.prefilled_buffer(
            self._start_symbol, length=self.order)
        if hasattr(self, "order_emissions"):
            order_emissions = self.order_emissions
        else:
            order_emissions = self.order
        last_emissions = utils.prefilled_buffer(
            self._start_symbol, length=order_emissions)
        generated_tokens = []
        while last_tokens[-1] != self._end_symbol:
            new_token = next_token(last_tokens)
            emission = emit(new_token, last_tokens, last_emissions)
            last_emissions.append(emission)
            generated_tokens.append(emission)
            last_tokens.append(new_token)
            # cut-off for max. emissions
            # + 1 for the start state
            if max_length is not None and max_length + 1 <= len(generated_tokens):
                break
        text = generated_tokens[:-1]
        return text

    def generate_text(self, max_length=None):
        """ Generates sentences from a given corpus
        max_length: maximum number of emissions
        Returns:
            Properly formatted string of generated sentences
        """
        return self._text_generator(next_token=self._generate_next_token, max_length=max_length)

    def _generate_next_token_helper(self, past_states, transitions):
        """ generates next token based previous states """
        key = tuple(past_states)
        assert key in transitions, "%s" % str(key)
        return utils.weighted_choice(transitions[key].items())

    def _generate_next_token(self, past_states):
        """ generates next token based previous words """
        return self._generate_next_token_helper(past_states, self.transitions)
