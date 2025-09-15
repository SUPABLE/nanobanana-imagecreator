import os
import uuid
import base64
import asyncio
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Load environment variables
load_dotenv()

app = FastAPI(title="Nano Banana Image Generator", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(MONGO_URL)
db = client.image_generator

# Models
class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., description="The text prompt for image generation")

class ImageGenerationResponse(BaseModel):
    id: str
    prompt: str
    image_url: str
    created_at: str
    success: bool = True

class GeneratedImage(BaseModel):
    id: str
    prompt: str
    image_data: str  # base64 encoded
    created_at: str

# Helper functions
def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data.get('created_at'), datetime):
        data['created_at'] = data['created_at'].isoformat()
    return data

def parse_from_mongo(item):
    """Parse datetime strings back from MongoDB"""
    if isinstance(item.get('created_at'), str):
        try:
            item['created_at'] = datetime.fromisoformat(item['created_at'])
        except ValueError:
            pass
    return item

@app.get("/")
async def root():
    return {"message": "Nano Banana Image Generator API", "status": "running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/api/generate-image", response_model=ImageGenerationResponse)
async def generate_image(request: ImageGenerationRequest):
    """Generate an image using Gemini Nano Banana model"""
    try:
        # Get the API key
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="API key not configured")
        
        # Create a unique session ID for this request
        session_id = str(uuid.uuid4())
        
        # Initialize LlmChat with Gemini model
        chat = LlmChat(
            api_key=api_key, 
            session_id=session_id, 
            system_message="You are an expert image generator that creates high-quality images based on text prompts."
        )
        chat.with_model("gemini", "gemini-2.5-flash-image-preview").with_params(modalities=["image", "text"])
        
        # Create the enhanced prompt
        enhanced_prompt = f"Create a high-quality, detailed image: {request.prompt}"
        
        # Generate the image
        msg = UserMessage(text=enhanced_prompt)
        text_response, images = await chat.send_message_multimodal_response(msg)
        
        if not images or len(images) == 0:
            raise HTTPException(status_code=500, detail="No images were generated")
        
        # Get the first image
        generated_image = images[0]
        image_data = generated_image['data']  # This is already base64 encoded
        
        # Create image record
        image_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc)
        
        image_record = {
            "id": image_id,
            "prompt": request.prompt,
            "image_data": image_data,
            "created_at": current_time.isoformat(),
        }
        
        # Store in MongoDB
        mongo_record = prepare_for_mongo(image_record.copy())
        await db.generated_images.insert_one(mongo_record)
        
        # Return response with data URL for display
        data_url = f"data:image/png;base64,{image_data}"
        
        return ImageGenerationResponse(
            id=image_id,
            prompt=request.prompt,
            image_url=data_url,
            created_at=current_time.isoformat(),
            success=True
        )
        
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate image: {str(e)}")

@app.get("/api/images", response_model=List[ImageGenerationResponse])
async def get_generated_images(limit: int = 10):
    """Get recently generated images"""
    try:
        # Fetch recent images from MongoDB
        cursor = db.generated_images.find().sort("created_at", -1).limit(limit)
        images = await cursor.to_list(length=None)
        
        # Convert to response format
        result = []
        for img in images:
            data_url = f"data:image/png;base64,{img['image_data']}"
            # Ensure created_at is a string
            created_at_str = img['created_at']
            if isinstance(created_at_str, datetime):
                created_at_str = created_at_str.isoformat()
            
            result.append(ImageGenerationResponse(
                id=img['id'],
                prompt=img['prompt'],
                image_url=data_url,
                created_at=created_at_str,
                success=True
            ))
        
        return result
        
    except Exception as e:
        print(f"Error fetching images: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch images: {str(e)}")

@app.delete("/api/images/{image_id}")
async def delete_image(image_id: str):
    """Delete a generated image"""
    try:
        result = await db.generated_images.delete_one({"id": image_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return {"success": True, "message": "Image deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)