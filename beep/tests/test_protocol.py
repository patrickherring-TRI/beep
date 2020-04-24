# Copyright 2019 Toyota Research Institute. All rights reserved.
"""Unit tests related to Generating protocol files"""

import os
import unittest
import json
import boto3
import datetime
from beep import PROCEDURE_TEMPLATE_DIR
from beep.generate_protocol import Procedure, \
    generate_protocol_files_from_csv
from monty.tempfile import ScratchDir
from monty.serialization import dumpfn, loadfn
from monty.os import makedirs_p
from botocore.exceptions import NoRegionError, NoCredentialsError
from beep.utils import os_format, hash_file
import difflib

TEST_DIR = os.path.dirname(__file__)
TEST_FILE_DIR = os.path.join(TEST_DIR, "test_files")


class ProcedureTest(unittest.TestCase):
    def setUp(self):
        # Determine events mode for testing
        try:
            kinesis = boto3.client('kinesis')
            response = kinesis.list_streams()
            self.events_mode = 'test'
        except NoRegionError or NoCredentialsError as e:
            self.events_mode = 'events_off'

    def test_io(self):
        test_file = os.path.join(TEST_FILE_DIR, 'xTESLADIAG_000003_CH68.000')
        json_file = os.path.join(TEST_FILE_DIR, 'xTESLADIAG_000003_CH68.json')
        test_out = 'test1.000'

        procedure = Procedure.from_file(os.path.join(TEST_FILE_DIR, test_file))
        with ScratchDir('.'):
            dumpfn(procedure, json_file)
            procedure.to_file(test_out)
            hash1 = hash_file(test_file)
            hash2 = hash_file(test_out)
            if hash1 != hash2:
                original = open(test_file).readlines()
                parsed = open(test_out).readlines()
                self.assertFalse(list(difflib.unified_diff(original, parsed)))
                for line in difflib.unified_diff(original, parsed):
                    self.assertIsNotNone(line)

        test_file = os.path.join(TEST_FILE_DIR, 'xTESLADIAG_000004_CH69.000')
        json_file = os.path.join(TEST_FILE_DIR, 'xTESLADIAG_000004_CH69.json')
        test_out = 'test2.000'

        procedure = Procedure.from_file(os.path.join(TEST_FILE_DIR, test_file))
        with ScratchDir('.'):
            dumpfn(procedure, json_file)
            procedure.to_file(test_out)
            hash1 = hash_file(test_file)
            hash2 = hash_file(test_out)
            if hash1 != hash2:
                original = open(test_file).readlines()
                parsed = open(test_out).readlines()
                self.assertFalse(list(difflib.unified_diff(original, parsed)))
                for line in difflib.unified_diff(original, parsed):
                    self.assertIsNotNone(line)

    def test_generate_proc_exp(self):
        test_file = os.path.join(TEST_FILE_DIR, 'EXP.000')
        json_file = os.path.join(TEST_FILE_DIR, 'EXP.json')
        test_out = 'test_EXP.000'
        test_parameters = ["4.2", "2.0C", "2.0C"]
        procedure = Procedure.from_exp(*test_parameters)
        with ScratchDir('.'):
            dumpfn(procedure, json_file)
            procedure.to_file(test_out)
            hash1 = hash_file(test_file)
            hash2 = hash_file(test_out)
            if hash1 != hash2:
                original = open(test_file).readlines()
                parsed = open(test_out).readlines()
                self.assertFalse(list(difflib.unified_diff(original, parsed)))
                for line in difflib.unified_diff(original, parsed):
                    self.assertIsNotNone(line)

    def test_missing(self):
        test_parameters = ["EXP", "4.2", "2.0C", "2.0C"]
        # TODO: okay to delete?
        # test_dict, sp = sdu.to_dict(
        #     os.path.join(templates, test_file),
        #     os.path.join(templates, json_file)
        # )
        # test_dict = sdu.maccor_format_dict(test_dict)
        template = os.path.join(TEST_FILE_DIR, "EXP_missing.000")
        self.assertRaises(UnboundLocalError, Procedure.from_exp,
                          *test_parameters[1:]+[template])

    def test_from_csv(self):
        csv_file = os.path.join(TEST_FILE_DIR, "parameter_test.csv")

        # Test basic functionality
        with ScratchDir('.') as scratch_dir:
            makedirs_p(os.path.join(scratch_dir, "procedures"))
            makedirs_p(os.path.join(scratch_dir, "names"))
            generate_protocol_files_from_csv(csv_file, scratch_dir)
            self.assertEqual(len(os.listdir(os.path.join(scratch_dir, "procedures"))), 3)

        # Test avoid overwriting file functionality
        with ScratchDir('.') as scratch_dir:
            makedirs_p(os.path.join(scratch_dir, "procedures"))
            makedirs_p(os.path.join(scratch_dir, "names"))
            dumpfn({"hello": "world"}, os.path.join("procedures", "name_000007.000"))
            generate_protocol_files_from_csv(csv_file, scratch_dir)
            post_file = loadfn(os.path.join("procedures", "name_000007.000"))
            self.assertEqual(post_file, {"hello": "world"})
            self.assertEqual(len(os.listdir(os.path.join(scratch_dir, "procedures"))), 3)

    def test_from_csv_2(self):
        csv_file = os.path.join(TEST_FILE_DIR, "PredictionDiagnostics_parameters.csv")

        # Test basic functionality
        with ScratchDir('.') as scratch_dir:
            makedirs_p(os.path.join(scratch_dir, "procedures"))
            makedirs_p(os.path.join(scratch_dir, "names"))
            generate_protocol_files_from_csv(csv_file, scratch_dir)
            self.assertEqual(len(os.listdir(os.path.join(scratch_dir, "procedures"))), 2)

            original = open(os.path.join(PROCEDURE_TEMPLATE_DIR, "diagnosticV2.000")).readlines()
            parsed = open(os.path.join(os.path.join(scratch_dir, "procedures"),
                                       "PredictionDiagnostics_000000.000")).readlines()
            self.assertFalse(list(difflib.unified_diff(original, parsed)))
            for line in difflib.unified_diff(original, parsed):
                self.assertIsNotNone(line)

            original = open(os.path.join(PROCEDURE_TEMPLATE_DIR, "diagnosticV3.000")).readlines()
            parsed = open(os.path.join(os.path.join(scratch_dir, "procedures"),
                                       "PredictionDiagnostics_000196.000")).readlines()
            diff = list(difflib.unified_diff(original, parsed))
            diff_expected = ['--- \n', '+++ \n', '@@ -27,7 +27,7 @@\n', '           <SpecialType> </SpecialType>\n',
             '           <Oper> = </Oper>\n', '           <Step>002</Step>\n', '-          <Value>03:00:00</Value>\n',
             '+          <Value>03:12:00</Value>\n', '         </EndEntry>\n', '         <EndEntry>\n',
             '           <EndType>Voltage </EndType>\n']
            self.assertEqual(diff, diff_expected)
            for line in difflib.unified_diff(original, parsed):
                self.assertIsNotNone(line)

            _, namefile = os.path.split(csv_file)
            namefile = namefile.split('_')[0] + '_names_'
            namefile = namefile + datetime.datetime.now().strftime("%Y%m%d_%H%M") + '.csv'
            names_test = open(os.path.join(scratch_dir, "names", namefile)).readlines()
            self.assertEqual(names_test, ['PredictionDiagnostics_000000_\n', 'PredictionDiagnostics_000196_\n'])

    @unittest.skip
    def test_from_csv_3(self):

        csv_file_list = os.path.join(TEST_FILE_DIR, "PreDiag_parameters - GP.csv")
        makedirs_p(os.path.join(TEST_FILE_DIR, "procedures"))
        makedirs_p(os.path.join(TEST_FILE_DIR, "names"))
        generate_protocol_files_from_csv(csv_file_list, TEST_FILE_DIR)
        if os.path.isfile(os.path.join(TEST_FILE_DIR, "procedures", ".DS_Store")):
            os.remove(os.path.join(TEST_FILE_DIR, "procedures", ".DS_Store"))
        self.assertEqual(len(os.listdir(os.path.join(TEST_FILE_DIR, "procedures"))), 265)

    def test_console_script(self):
        csv_file = os.path.join(TEST_FILE_DIR, "parameter_test.csv")

        # Test script functionality
        with ScratchDir('.') as scratch_dir:
            # Set BEEP_ROOT directory to scratch_dir
            os.environ['BEEP_ROOT'] = os.getcwd()
            procedures_path = os.path.join("data-share", "protocols", "procedures")
            names_path = os.path.join("data-share", "protocols", "names")
            makedirs_p(procedures_path)
            makedirs_p(names_path)

            # Test the script
            json_input = json.dumps(
                {"file_list": [csv_file],
                 "mode": self.events_mode})
            os.system("generate_protocol {}".format(os_format(json_input)))
            self.assertEqual(len(os.listdir(procedures_path)), 3)
