###
# Created Date: Wednesday, October 18th 2023, 12:36:49 pm
# Author: Bin Wang
# -----
# Copyright (c) Bin Wang @ bwang28c@gmail.com
# 
# -----
# HISTORY:
# Date&Time 			By	Comments
# ----------			---	----------------------------------------------------------
###


MODEL_PATH='binwang/InstructDS'

export CUDA_VISIBLE_DEVICES=0

python src/demo_page.py \
    --model_path $MODEL_PATH 
