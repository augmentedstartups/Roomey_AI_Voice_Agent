import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Add parent directory to path to import from utils if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def generate_linkedin_post(topic, context="", temperature=0.1, model="openai/gpt-4.1"):
    """
    Generate a LinkedIn post using OpenRouter API with Gemini model.
    
    Args:
        topic (str): The topic for the LinkedIn post
        context (str): Additional context or knowledge to include
        temperature (float): Controls randomness in output (0.0-1.0)
        model (str): The model to use via OpenRouter (default: openai/gpt-4.1)
        
    Returns:
        dict: The generated LinkedIn post data with metadata
    """
    print("\n🤖 Initializing LinkedIn Post Generation...")
    print(f"📚 Topic: {topic}")
    print(f"🧠 Model: {model}")
    
    # Initialize OpenRouter client
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    
    # LinkedIn post system prompt
    system_prompt = """
    Generate a LinkedIn post in the highly engaging and viral style of a motivational influencer like Anisha Jain. The post should be structured for maximum readability and impact.

    **Follow these stylistic and structural guidelines precisely:**

    1.  **Opening Hook:**
        * Begin with 1-2 very short, bold, and punchy sentences. This should be a captivating statement that is relatable, slightly contrarian, or addresses a common pain point.
        * Each sentence should be on a new line.

    2.  **Elaboration/Bridge:**
        * Follow the hook with 1-3 additional short sentences that elaborate on the opening or smoothly transition to the main message.
        * Each sentence on a new line.

    3.  **Introduction to List:**
        * Introduce your main points with a phrase like: "Here's why:", "Here are X truths:", "Consider these X points:", "Here's what to do:". This phrase should be on its own line.

    4.  **Main Content - Numbered List:**
        * Create a numbered list with 3 to 7 points.
        * Each numbered item should be a concise statement, on its own line.
        * **Crucial Detail:** For each numbered item, provide one or two brief elaborations or explanations. Each elaboration MUST start on a new line and be preceded by the arrow symbol '↳ '.
            * Example of a list item:
                "1. Action Breeds Momentum
                ↳ The first step is often the hardest.
                ↳ Once you start, inertia works in your favor."

    5.  **Formatting & Style:**
        * **Line Breaks:** Use new lines extensively. Almost every short sentence or distinct phrase should be a new paragraph. This creates significant white space.
        * **Capitalization:** Use standard sentence case. You may use ALL CAPS for a single word or very short phrase (1-3 words) if you want to create strong emphasis (use sparingly).
        * **Language:** Keep the language simple, direct, and highly motivational. Address the reader using "you." Avoid jargon or complex sentence structures.
        * **Tone:** Confident, encouraging, inspiring, and slightly assertive. Aim to empower the reader and cut through common excuses.

    6.  **Concluding Thought (Optional but Recommended):**
        * After the list, you can add 1-2 short sentences that summarize the key message or offer a final piece of powerful encouragement. Each sentence on a new line.

    7.  **Standard Call to Action (CTA):**
        * The post MUST end with the following two lines, formatted exactly like this:
            "♻️ Repost this if you agree.
            Follow @Ritesh Kanjee and @Augmented AI to never miss a post."

    Do not be cheesy or salesey.
    """
    
    # User prompt with topic and context
    user_prompt = f"""Create a LinkedIn post about '{topic}'.
    
    Use this additional context if helpful: {context}
    
    Follow all instructions in the system prompt regarding formatting and structure.
    """
    
    print("📝 Generating LinkedIn post...")
    
    # Define JSON schema for structured output
    json_schema = {
        "type": "object",
        "properties": {
            "post_content": {
                "type": "string",
                "description": "The full formatted LinkedIn post content"
            }
        },
        "required": ["post_content"],
        "additionalProperties": False
    }
    
    # Make API call to OpenRouter
    response = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "https://augmentedstartups.com",
            "X-Title": "LinkedIn Post Generator",
        },
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        max_tokens=2000,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "linkedin_post",
                "strict": True,
                "schema": json_schema
            }
        }
    )
    
    content = response.choices[0].message.content
    print("\nRaw response content:")
    print(content)  # Print for debugging
    
    try:
        # Parse the JSON response
        post_data = json.loads(content)
        print("\nJSON parsed successfully!")
        
        if 'post_content' not in post_data:
            raise ValueError("Invalid post format: missing 'post_content' field")
        
        # Add metadata to the post data
        post_data['topic'] = topic
        post_data['context'] = context
        post_data['generated_at'] = datetime.now().isoformat()
        
        model_name = model.split('/')[-1] if '/' in model else model
        return post_data, model_name
    
    except json.JSONDecodeError as e:
        print(f"\nJSON Parse Error: {str(e)}")
        raise

def save_linkedin_post(post_data, model_name, topic_slug=None):
    """Save the LinkedIn post data to a JSON file and markdown file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a slug from topic if not provided
    if not topic_slug:
        topic_slug = post_data['topic'].lower().replace(' ', '_')[:30]
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f'{output_dir}/linkedin_post_{topic_slug}_{timestamp}.json'
    md_filename = f'{output_dir}/linkedin_post_{topic_slug}_{timestamp}.md'
    
    # Save as JSON
    with open(json_filename, 'w') as f:
        json.dump(post_data, f, indent=2)
    
    # Save as Markdown
    with open(md_filename, 'w') as f:
        # Add title as H1
        f.write(f"# {post_data['topic']}\n\n")
        # Add post content (already formatted with line breaks)
        f.write(post_data['post_content'])
        # Add metadata at the bottom
        f.write(f"\n\n---\n")
        f.write(f"Generated: {post_data['generated_at']}\n")
    
    print(f"LinkedIn post saved to JSON: {json_filename}")
    print(f"LinkedIn post saved to Markdown: {md_filename}")
    
    # Return both filenames as a dictionary
    return {"json": json_filename, "markdown": md_filename}

def format_linkedin_post(context):
    """
    Generate a LinkedIn post using only context as input.
    The function will extract a topic from the context automatically.
    
    Args:
        context (str): The context information to use for generating the LinkedIn post
        
    Returns:
        str: A status message indicating success or failure
    """
    if not context or not isinstance(context, str) or len(context.strip()) < 10:
        return "Error: Context is too short or invalid. Please provide more detailed information."
    
    try:
        # Extract a topic from the context
        # Initialize OpenRouter client for topic extraction
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        
        # Extract topic from context
        topic_prompt = f"Given the following context, generate a concise topic (3-7 words) for a LinkedIn post. Only return the topic, nothing else.\n\nContext: {context}"
        
        topic_response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://augmentedstartups.com",
                "X-Title": "LinkedIn Topic Extractor",
            },
            model="openai/gpt-4.1",
            messages=[
                {"role": "user", "content": topic_prompt}
            ],
            temperature=0.1,
            max_tokens=20
        )
        
        topic = topic_response.choices[0].message.content.strip()
        print(f"📌 Extracted topic: {topic}")
        
        # Generate LinkedIn post with the extracted topic
        post_data, model_name = generate_linkedin_post(topic, context)
        
        # Save to files (returns dict with 'json' and 'markdown' paths)
        files = save_linkedin_post(post_data, model_name)
        
        return f"LinkedIn post about '{topic}' successfully generated and saved to:\nJSON: {files['json']}\nMarkdown: {files['markdown']}"
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n❌ Error in format_linkedin_post: {e}\n{error_details}")
        return f"Error generating LinkedIn post: {str(e)}"

# Example usage
if __name__ == "__main__":
    # Example context
    context = """
    NVIDIA is a leading hardware company that designs and manufactures GPUs essential for AI development.
    OpenAI is an AI research lab that creates advanced AI models like GPT-4.
    NVIDIA has recently reached a $3 trillion market cap, while OpenAI is valued at around $80 billion.
    NVIDIA provides the hardware infrastructure that powers AI, while OpenAI develops the models that run on this hardware.
    Both companies are competing for AI talent and resources in the rapidly growing AI industry.
    """
    
    # Test the new function that takes only context
    result = format_linkedin_post(context)
    print(f"\nResult: {result}")
    
    # Alternatively, you can still use the original function directly
    try:
        # Generate LinkedIn post with explicit topic
        topic = "NVIDIA versus OpenAI"
        post_data, model_name = generate_linkedin_post(topic, context)
        
        # Save to files (returns dict with 'json' and 'markdown' paths)
        files = save_linkedin_post(post_data, model_name)
        
        # Print the generated post content
        print("\n" + "=" * 80)
        print("GENERATED LINKEDIN POST:")
        print("=" * 80)
        print(post_data['post_content'])
        print("=" * 80)
        print(f"\n✅ LinkedIn post successfully generated and saved to:")
        print(f"JSON: {files['json']}")
        print(f"Markdown: {files['markdown']}")
        
    except Exception as e:
        print(f"\n❌ Error generating LinkedIn post: {e}")
        import traceback
        traceback.print_exc()
