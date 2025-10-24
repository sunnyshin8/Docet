
# import os
# import json
# import torch
# from typing import List, Dict, Any, Optional
# from transformers import (
#     AutoTokenizer, 
#     AutoModelForCausalLM, 
#     AutoModelForSeq2SeqLM,
#     pipeline, 
#     TrainingArguments, 
#     Trainer,
#     DataCollatorForLanguageModeling
# )
# from peft import LoraConfig, get_peft_model, TaskType
# from datasets import Dataset
# import logging

# from ..config import settings

# logger = logging.getLogger(__name__)


# class LocalLLMService:
    
#     def __init__(self, model_name: str = "Qwen/Qwen2-0.5B-Instruct"):
#         self.model_name = model_name
#         self.model_path = "./data/models/fine_tuned"
#         self.model = None
#         self.tokenizer = None
#         self.pipeline = None
#         self.mock_mode = True
        
#         os.makedirs(self.model_path, exist_ok=True)
    
#     async def load_model(self, use_fine_tuned: bool = True):
        
#         self.mock_mode = False
        
#         try:
#             if use_fine_tuned and os.path.exists(os.path.join(self.model_path, "config.json")):
#                 logger.info("Loading fine-tuned model...")
#                 model_path = self.model_path
#             else:
#                 logger.info(f"Loading base model: {self.model_name}")
#                 model_path = self.model_name
            
#             self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            
#             if "t5" in self.model_name.lower():
#                 self.model = AutoModelForSeq2SeqLM.from_pretrained(
#                     model_path,
#                     torch_dtype=torch.float32,
#                     device_map="cpu",
#                     low_cpu_mem_usage=True
#                 )
#                 pipeline_task = "text2text-generation"
#             else:
#                 self.model = AutoModelForCausalLM.from_pretrained(
#                     model_path,
#                     torch_dtype=torch.float32,
#                     device_map="cpu",
#                     low_cpu_mem_usage=True
#                 )
#                 pipeline_task = "text-generation"
            
#             if self.tokenizer.pad_token is None:
#                 self.tokenizer.pad_token = self.tokenizer.eos_token
            
#             self.pipeline = pipeline(
#                 pipeline_task,
#                 model=self.model,
#                 tokenizer=self.tokenizer,
#                 device_map="cpu"
#             )
            
#             logger.info(f"Model {self.model_name} loaded successfully!")
            
#         except Exception as e:
#             logger.error(f"Failed to load model: {e}")
#             self.mock_mode = True
#             raise
    
#     async def generate_response(
#         self, 
#         prompt: str, 
#         max_length: int = 512,
#         temperature: float = 0.7,
#         do_sample: bool = True
#     ) -> str:
        
#         if self.mock_mode:
#             return f"Mock response to: {prompt[:50]}... [Enable real model in /api/v1/training/model/load]"
        
#         if self.pipeline is None:
#             await self.load_model()
        
#         try:
#             if "t5" in self.model_name.lower() or "flan" in self.model_name.lower():
#                 response = self.pipeline(
#                     prompt,
#                     max_length=80,
#                     temperature=temperature,
#                     do_sample=do_sample,
#                     num_return_sequences=1,
#                     truncation=True,
#                     repetition_penalty=1.5,
#                     early_stopping=True
#                 )
#                 generated_text = response[0]['generated_text'].strip()
#             elif "qwen" in self.model_name.lower():
#                 response = self.pipeline(
#                     prompt,
#                     max_new_tokens=80,
#                     temperature=temperature,
#                     do_sample=do_sample,
#                     pad_token_id=self.tokenizer.eos_token_id,
#                     eos_token_id=self.tokenizer.eos_token_id,
#                     num_return_sequences=1,
#                     truncation=True,
#                     repetition_penalty=1.3
#                 )
                
#                 generated_text = response[0]['generated_text']
#                 if generated_text.startswith(prompt):
#                     generated_text = generated_text[len(prompt):].strip()
#             elif "phi" in self.model_name.lower():
#                 messages = [{"role": "user", "content": prompt}]
                
#                 if hasattr(self.tokenizer, 'apply_chat_template'):
#                     formatted_prompt = self.tokenizer.apply_chat_template(
#                         messages, 
#                         tokenize=False, 
#                         add_generation_prompt=True
#                     )
#                 else:
#                     formatted_prompt = f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
                
#                 response = self.pipeline(
#                     formatted_prompt,
#                     max_new_tokens=100,
#                     temperature=temperature,
#                     do_sample=do_sample,
#                     pad_token_id=self.tokenizer.eos_token_id,
#                     eos_token_id=self.tokenizer.eos_token_id,
#                     num_return_sequences=1,
#                     truncation=True,
#                     repetition_penalty=1.2
#                 )
                
#                 generated_text = response[0]['generated_text']
#                 if formatted_prompt in generated_text:
#                     generated_text = generated_text[len(formatted_prompt):].strip()
#             else:
#                 if "DialoGPT" in self.model_name:
#                     conversation_prompt = f"Human: {prompt}\nBot:"
#                 else:
#                     conversation_prompt = prompt
                
#                 response = self.pipeline(
#                     conversation_prompt,
#                     max_new_tokens=50,
#                     temperature=temperature,
#                     do_sample=do_sample,
#                     pad_token_id=self.tokenizer.eos_token_id,
#                     eos_token_id=self.tokenizer.eos_token_id,
#                     num_return_sequences=1,
#                     truncation=True
#                 )
#                 generated_text = response[0]['generated_text']
                
#                 if "DialoGPT" in self.model_name:
#                     if "Bot:" in generated_text:
#                         generated_text = generated_text.split("Bot:")[-1].strip()
#                 else:
#                     if generated_text.startswith(conversation_prompt):
#                         generated_text = generated_text[len(conversation_prompt):].strip()
            
#             return generated_text
            
#         except Exception as e:
#             logger.error(f"Failed to generate response: {str(e)}")
#             return "I apologize, but I'm unable to generate a response at the moment."
    
#     async def prepare_training_data(self, documents: List[Dict[str, Any]]) -> Dataset:
#         training_texts = []
        
#         for doc in documents:
#             content = doc.get('content', '')
#             title = doc.get('title', 'Documentation')
            
#             training_example = self._create_training_example(title, content)
#             training_texts.append(training_example)
        
#         dataset = Dataset.from_dict({"text": training_texts})
#         return dataset
    
#     def _create_training_example(self, title: str, content: str) -> str:
#         return f"""<|system|>You are a helpful AI assistant that answers questions about {title} documentation. Provide accurate and helpful responses based on the documentation.<|endoftext|>
# <|user|>What is this documentation about?<|endoftext|>
# <|assistant|>{content[:500]}...<|endoftext|>"""
    
#     async def fine_tune_model(
#         self, 
#         training_dataset: Dataset,
#         learning_rate: float = 5e-4,
#         num_epochs: int = 3,
#         batch_size: int = 4
#     ):
#         logger.info("Starting model fine-tuning...")
        
#         if self.model is None:
#             await self.load_model(use_fine_tuned=False)
        
#         lora_config = LoraConfig(
#             task_type=TaskType.CAUSAL_LM,
#             inference_mode=False,
#             r=16,
#             lora_alpha=32,
#             lora_dropout=0.1,
#             target_modules=["q_proj", "v_proj"]  # Target attention layers
#         )
        
#         model = get_peft_model(self.model, lora_config)
        
#         def tokenize_function(examples):
#             return self.tokenizer(
#                 examples["text"], 
#                 truncation=True, 
#                 padding=True, 
#                 max_length=512
#             )
        
#         tokenized_dataset = training_dataset.map(tokenize_function, batched=True)
        
#         training_args = TrainingArguments(
#             output_dir=self.model_path,
#             overwrite_output_dir=True,
#             num_train_epochs=num_epochs,
#             per_device_train_batch_size=batch_size,
#             gradient_accumulation_steps=4,
#             warmup_steps=100,
#             learning_rate=learning_rate,
#             fp16=False,
#             logging_steps=50,
#             save_steps=500,
#             evaluation_strategy="no",
#             save_strategy="epoch",
#             load_best_model_at_end=False,
#             report_to=None,
#         )
        
#         data_collator = DataCollatorForLanguageModeling(
#             tokenizer=self.tokenizer,
#             mlm=False
#         )
        
#         trainer = Trainer(
#             model=model,
#             args=training_args,
#             train_dataset=tokenized_dataset,
#             data_collator=data_collator,
#         )
        
#         trainer.train()
        
#         trainer.save_model(self.model_path)
#         self.tokenizer.save_pretrained(self.model_path)
        
#         logger.info(f"Model fine-tuned and saved to: {self.model_path}")
    
#     async def get_model_info(self) -> Dict[str, Any]:
#         info = {
#             "base_model": self.model_name,
#             "model_path": self.model_path,
#             "fine_tuned_available": os.path.exists(os.path.join(self.model_path, "config.json")),
#             "model_loaded": self.model is not None
#         }
        
#         if self.model is not None:
#             info["model_parameters"] = sum(p.numel() for p in self.model.parameters())
#             info["trainable_parameters"] = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
#         return info


# local_llm_service = LocalLLMService()

# def get_local_llm_service() -> LocalLLMService:
#     return local_llm_service