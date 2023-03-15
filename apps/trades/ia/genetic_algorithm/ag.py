import json
from apps.trades.ia.utils.binary_tree import (
    BinaryTree
)

from multiprocessing import Pool
import random

from apps.trades.ia.binance_client_utils.utils import format_decimals

# Genetic algorithm


class Individual:

    def __init__(self,
                 _encoded_variables,
                 _mutation_intensity,
                 _dna=None
                 ):
        self.encoded_variables = _encoded_variables
        self.mutation_intensity = _mutation_intensity 
        self.length = self.calculate_dna_length_from_encoded_variables()
        self.dna = _dna if _dna else self.generate_individual()
        self.score = 0
        self.score_long = 0
        self.score_short = 0
        self.variables = {}
        self.variable_to_optimize = "score"

    def set_variable_to_optimize(self, variable):
        self.variable_to_optimize = variable

    def get_variable_value_to_optimize(self):
        if self.variable_to_optimize == "short":
            return self.score_short
        if self.variable_to_optimize == "long":
            return self.score_long
        return self.score

    def calculate_dna_length_from_encoded_variables(self):
        length = 0
        for i in self.encoded_variables.keys():
            length += self.encoded_variables[i]["length_dna"]
        return length

    def generate_individual(self):
        """Generate n bits strings individual

        :param nbits: String length simulating the bits quantity
        :type nbits: int

        """
        count = 0
        individual = ""
        while(count < self.length):
            individual += str(random.randint(0, 1))
            count += 1
        return individual

    def decode_dna_variables_to_decimal(self):
        genes = self.cut_dna()
        decoded_variables = {}
        for gen in genes:
            decoded_variables[gen["variable"]] = self.binary_to_decimal(
                gen["dna"], 
                gen["min_value"], 
                gen["max_value"]
            )
        return decoded_variables

    def cut_dna(self):
        lengths = self.get_lengths_from_encoded_variables()
        genes = []
        for l in lengths:
            genes += [
                {
                    "dna": self.dna[l["init"]:l["end"]],
                    "min_value": l["min_value"],
                    "max_value": l["max_value"],
                    "variable": l["variable"]
                }
            ]
        return genes

    def mutation(self):
        bin = list(self.dna)
        for _ in range(random.randint(0, self.mutation_intensity)):
            rand = random.randint(0, self.length - 1)
            if(bin[rand] == "0"):
                bin[rand] = "1"
            if(bin[rand] == "1"):
                bin[rand] = "0"
        self.dna = "".join(bin)

    def set_score(self, _score):
        self.score = _score

    def set_score_long(self, _score_long):
        self.score_long = _score_long

    def set_score_short(self, _score_short):
        self.score_short = _score_short

    def set_variable_result(self, _result):
        self.variables = _result

    def get_variable_result(self):
        return self.variables

    def get_lengths_from_encoded_variables(self):
        lengths = []
        init = 0
        for i in self.encoded_variables.keys():
            length_dna = self.encoded_variables[i]["length_dna"]
            lengths += [
                {
                    "init": init,
                    "end": init + length_dna,
                    "min_value": self.encoded_variables[i]["min_value"],
                    "max_value": self.encoded_variables[i]["max_value"],
                    "variable": i,
                }
            ]
            init += length_dna
        return lengths

    @staticmethod
    def binary_to_decimal(gen, a, b):
        """ Converts binary values into a decimal values with one comma, between 
        [a,b] interval

        :param bin: String binary value
        :type bin: String:
        :param a: Start interval
        :type a: int
        :param b: End interval
        :type b: int
        """
        n_count = len(gen)
        n = n_count
        dec = 0
        for i in gen:
            if i == '1':
                dec += 2**(n_count-1)
            n_count -= 1
        return a+((dec)/(2**n-1))*(b-a)
    
    def __str__(self):
        return self.dna




class Population:

    def __init__(self,
                 _quantity,
                 _encoded_variables,
                 _mutation_intensity,
                 ):
        self.quantity = _quantity
        self.encoded_variables = _encoded_variables
        self.mutation_intensity = _mutation_intensity
        self.score = 0
        self.population = self.generate_population()

    def generate_population(self):
        population = []
        count = 0
        while(count < self.quantity):
            individual = Individual(
                _encoded_variables=self.encoded_variables,
                _mutation_intensity=self.mutation_intensity,
            )
            population.append(individual)
            count += 1
        return population


    def breed(self):
        """
        Reproduction function, cross the gen for two individuals, uniform cross.
        :param bin1: One individual
        """
        self.__order_by_individual_score()
        half = int(self.quantity/2)
        best_half = self.population[half:]
        ten_percent = int(self.quantity/10)
        best_ten_percent = self.population[ten_percent:]

        new_population = []
        for _ in range(half * 2):
            mother = best_half[random.randint(0, half - 1)]
            father = best_half[random.randint(0, half - 1)]
            new_population.append(
                self.__cross_genes(
                    father,
                    mother
                )
            )

        current_generation = best_half
        new_quantity = self.quantity - len(current_generation)
        # new_population = self.generate_population()
        while new_quantity > 0:
            current_generation.append(new_population[new_quantity])
            new_quantity -= 1

        self.population = current_generation

    def __order_by_individual_score(self):
        self.population.sort(
            key=lambda individual: individual.get_variable_value_to_optimize()
        )

    def __cross_genes(self, father, mother):
        son_dna = ""
        for i in range(father.length):
            rand = random.randint(0, 1)
            if (rand == 0):
                son_dna += father.dna[i]
            else:
                son_dna += mother.dna[i]
        son = Individual(
            _encoded_variables=father.encoded_variables,
            _mutation_intensity=father.mutation_intensity,
            _dna=son_dna,
        )
        son.mutation()
        return son

    def calculate_population_score(self):
        self.__order_by_individual_score()
        return self.population[-1].score

    def get_best_individual(self):
        self.__order_by_individual_score()
        best_individual = self.population[-1]
        score = best_individual.score
        score_long = best_individual.score_long
        score_short = best_individual.score_short
        constants = best_individual.get_variable_result()
        return  score, score_long, score_short, constants, best_individual

class GeneticAlgorithm:
    def __init__(self,
                 _population_min,
                 _population_max,
                 _individual_encoded_variables,
                 _individual_muatition_intensity,
                 _strategy,
                 _klines,
                 _client
                 ):
        self.individual_encoded_variables = _individual_encoded_variables
        other_info = {
            "score_short": 0,
            "score_long": 0
        }
        self.evaluated = BinaryTree(0, 0, other_info)
        self.strategy = _strategy
        self.klines = _klines
        self.client= _client

        self.population_min = _population_min
        self.population_max = _population_max
        self.individual_muatition_intensity = _individual_muatition_intensity

        self.population = Population(
            _quantity=random.randint(self.population_min, self.population_max),
            _encoded_variables= self.individual_encoded_variables,
            _mutation_intensity=self.individual_muatition_intensity,
        )

    def restart_population(self):
        self.population = Population(
            _quantity=random.randint(self.population_min, self.population_max),
            _encoded_variables= self.individual_encoded_variables,
            _mutation_intensity=self.individual_muatition_intensity,
        )

    def evolution(self, generations, static_info):
        if type(static_info) != dict:
            static_info = json.loads(static_info)

        to_evaluate = ["score"]

        bests = {}

        for te in to_evaluate:
            print(f"@@@@@@@@@@@@ OPTIMIZE {te} @@@@@@@@@@@@@@@@@@")
            for gen in range(generations):
                t = Pool(processes=12)
                data = []
                for individual in self.population.population:
                    individual.set_variable_to_optimize(te)
                    data.append(
                        {
                            'individual': individual,
                            'info': static_info
                        }
                    )
                individuals = t.map(self.optimized_individual_function, data)
                t.close()
                self.population.population = individuals
                score = self.population.get_best_individual()
                print(f"Gen {gen}:")
                print(f"score: {score[0]}, score_long: {score[1]}, score_short: {score[2]} ")
                self.population.breed()

            bests[te] = self.get_greatest_individual()

            self.restart_population()
        
        return bests["score"]

    def optimized_individual_function(self, data):
        individual = data['individual']
        info = data['info']

        values = individual.decode_dna_variables_to_decimal()

        for i in self.individual_encoded_variables.keys():
            val = values[i]
            if type(val) == int or type(val) == float:
                val = format_decimals(val)
            info[i] = val

        info["interval"] = int(info["interval"])

        # exists_tree, val_tree, other_info = self.evaluated.search(individual.dna)
        # if exists_tree is not False and val_tree is not None:
        #     individual.set_score(val_tree)
        #     individual.set_score_long(other_info["score_long"])
        #     individual.set_score_short(other_info["score_short"])
        #     individual.set_variable_result(info)
        #     return individual

        # other_info = {
        #     "score_short": individual.score_short,
        #     "score_long": individual.score_long
        # }

        # self.evaluated.insert(individual.dna, individual.score, other_info)

        # if (
        #     info["stop_loss_divisor_plus"] > (info["stop_loss_percent"] / 2) or 
        #     info["stop_loss_divisor_plus_short"] > (info["stop_loss_percent_short"] / 2)
        #     ):
        #     individual.set_variable_result(info)
        #     individual.set_score(-1)
        #     individual.set_score_long(-1)
        #     individual.set_score_short(-1)
        #     return individual

        evaluated = self.strategy(client=self.client).backtesting(info, "ga", self.klines)

        individual.set_variable_result(info)
        individual.set_score(evaluated.score)
        individual.set_score_long(evaluated.score_long)
        individual.set_score_short(evaluated.score_short)


        return individual

    def get_greatest_individual(self):
        return self.population.get_best_individual()
