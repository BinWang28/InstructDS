#!/usr/bin/env python
# -*- coding:utf-8 -*-
###
# Created Date: Thursday, October 19th 2023, 10:18:47 am
# Author: Bin Wang
# -----
# Copyright (c) Bin Wang @ bwang28c@gmail.com
# 
# -----
# HISTORY:
# Date&Time 			By	Comments
# ----------			---	----------------------------------------------------------
###

import sys
import json

import fire
import gradio as gr
import torch
from transformers import GenerationConfig, T5Tokenizer, T5ForConditionalGeneration




def main(
    model_path: str = "",
    server_name: str = "0.0.0.0",  # Allows to listen on all interfaces by providing '0.
):

    # Loda data
    all_data_samples = []
    datasets = ['SAMSum', 'SAMSum_QDS','DialogSum','DialogSum_QDS', 'TODSum', 'TODSum_QDS', 'DREAM']
    for dataset in datasets:
        with open('data/{}/test.json'.format(dataset), 'r') as f:
            data = json.load(f)
            all_data_samples.append(data)

    # Load model
    tokenizer = T5Tokenizer.from_pretrained(model_path, cache_dir="cache")
    model     = T5ForConditionalGeneration.from_pretrained(model_path, device_map="auto", cache_dir='cache', torch_dtype=torch.float16)
    model.eval()
    if torch.__version__ >= "2" and sys.platform != "win32":
        model = torch.compile(model)

    # Inference
    def evaluate(
        question       = None,
        dialogue       = None,
        dataset_index  = None,
        sample_index   = None,
        output_length  = None,
        **kwargs,
    ):
        

        temperature    = 0.7
        top_p          = 0.75
        top_k          = 40
        num_beams      = 8
        max_new_tokens = 128
    
        dataset_data = all_data_samples[dataset_index-1]
        instruction = dataset_data[0]['instruction']

        if question == '' or dialogue == '':
            if sample_index > len(dataset_data):
                sample_index = len(dataset_data)
                
            if 'question' in dataset_data[sample_index-1]:
                question = dataset_data[sample_index-1]['question']
            else:
                question = ''
            dialogue = dataset_data[sample_index-1]['dialogue']

        if output_length != 0:
            output_length_instruction = 'The output should be {} words long.'.format(output_length)
        else:
            output_length_instruction = ''


        if question == '':
            if output_length_instruction == '':
                input_to_model = '###Instruction:\n{}\n### Input:\n{}\n'.format(instruction, dialogue)
            else:
                input_to_model = '###Instruction:\n{} {}\n### Input:\n{}\n'.format(instruction, output_length_instruction, dialogue)

        else:
            if output_length_instruction == '':
                input_to_model = '###Instruction:\n{} {}\n### Input:\n{}\n'.format(instruction, question, dialogue)
            else:
                input_to_model = '###Instruction:\n{} {} {}\n### Input:\n{}\n'.format(instruction, question, output_length_instruction, dialogue)

        print(input_to_model)
        
        inputs = tokenizer(input_to_model, return_tensors="pt")
        input_ids = inputs["input_ids"].to('cuda')

        generation_config = GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            num_beams=num_beams,
            do_sample=True,
            **kwargs,
        )

        with torch.no_grad():
            generation_output = model.generate(
                input_ids               = input_ids,
                generation_config       = generation_config,
                return_dict_in_generate = True,
                output_scores           = True,
                max_new_tokens          = max_new_tokens,
            )
        output_sequence = generation_output.sequences[0]
        output = tokenizer.decode(output_sequence, skip_special_tokens=True)

        if question == '':
            question = "No quesiton provided. Below is a general summarization of the dialogue."

        print(output)

        return question, dialogue, output


    gr.Interface(
        fn=evaluate,
        inputs=[
            gr.components.Textbox(
                lines=2,
                label="Question",
                placeholder="Input your own question. Leave it blank to extract directly from the dataset.",
            ),

            gr.components.Textbox(
                lines=5, 
                label="Dialogue", 
                placeholder="Input your own dialogue. Leave it blank to extract directly from the dataset."),
            
            gr.components.Slider(
                minimum=1, 
                maximum=7, 
                step=1,
                value=1, 
                label="Dataset Index"
            ),

            gr.components.Slider(
                minimum=1, 
                maximum=2041, 
                step=1,
                value=1, 
                label="Sample Index"
            ),

              gr.components.Slider(
                minimum=0, 
                maximum=30, 
                step=1,
                value=0, 
                label="Perferred Output Length"
            ),

        ],
        outputs=[
            gr.components.Textbox(
                lines=2,
                label="Question",
            ),
            gr.components.Textbox(
                lines=6,
                label="Dialogue",
            ),
            gr.components.Textbox(
                lines=4,
                label="Summary",
            ),

        ],
        allow_flagging="auto",
        title="InsructDS - EMNLP 2023",
        description="A demo page for https://arxiv.org/abs/2310.10981",
    ).queue().launch(server_name=server_name, server_port=8080, share=False)
    


if __name__ == "__main__":
    fire.Fire(main)
