from django.test import TestCase
from apps.trades.ia.genetic_algorithm.ag import (
    Individual,
)

from apps.trades.ia.genetic_algorithm.function import (
    BTCBUSDTraderFunction
)

import random

# Genetic Algorithm tests

class IndividualTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.length = 0
        self.mutation_intensity = 0
        self.individual = None
        
    def setUp(self):
        self.length = random.randint(0, 1000)
        self.mutation_intensity = random.randint(0, 1000)
        self.individual = Individual(self.length, self.mutation_intensity)
                 
    def test_generate_individual(self):
        self.assertIsNotNone(self.length)
        self.assertIsNotNone(self.mutation_intensity)
        self.assertIsNotNone(self.individual)
        
        self.assertEqual(self.length, self.individual.length)
        self.assertEqual(self.length, len(self.individual.dna))
        self.assertEqual(0, self.individual.score)
        self.assertTrue(1 < self.individual.mutation_intensity < self.mutation_intensity)
        
    def test_binary_to_decimal(self):
        pass
        