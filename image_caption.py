from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForCausalLM, BlipForConditionalGeneration#, Blip2ForConditionalGeneration



class ImageCaption:
    def __init__(self, device: str = "cpu"):
        self.device = device
        module_and_path = (BlipForConditionalGeneration, "Salesforce/blip-image-captioning-base")
        self.caption_model = module_and_path[0].from_pretrained(module_and_path[1], torch_dtype=torch.float32).to(self.device)
        self.caption_processor = AutoProcessor.from_pretrained(module_and_path[1])
    

    def generate_caption(self, image: Image.Image | str) -> str:
        if isinstance(image, str):
            if image.startswith("http") or image.startswith("data:"):
                import urllib.request
                from io import BytesIO
                image = Image.open(BytesIO(urllib.request.urlopen(image).read())).convert("RGB")
            else:
                image = Image.open(image).convert("RGB")
        inputs = self.caption_processor(images=image, return_tensors="pt").to(self.device)
        tokens = self.caption_model.generate(**inputs, max_new_tokens=100)
        return self.caption_processor.batch_decode(tokens, skip_special_tokens=True)[0].strip()
