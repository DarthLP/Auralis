#!/usr/bin/env python3
import json
import re

def extract_json_from_text(text):
    # Look for JSON blocks in the text
    json_patterns = [
        r'```json\s*(\{.*?\})\s*```',  # JSON in code blocks
        r'```\s*(\{.*?\})\s*```',      # JSON in generic code blocks
        r'(\{[^{}]*"score"[^{}]*\})',  # JSON with score field
        r'(\{[^{}]*"primary_category"[^{}]*\})',  # JSON with primary_category field
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                # Try to parse as JSON to validate
                json.loads(match)
                return match
            except json.JSONDecodeError:
                continue
    
    # Try to find any JSON object in the text
    json_obj_pattern = r'\{[^{}]*\}'
    matches = re.findall(json_obj_pattern, text, re.DOTALL)
    for match in matches:
        try:
            # Try to parse as JSON to validate
            parsed = json.loads(match)
            # Check if it has the expected fields
            if 'score' in parsed or 'primary_category' in parsed:
                return match
        except json.JSONDecodeError:
            continue
    
    # If no JSON found, return the original text
    return text

# Test with the actual response we got
test_text = '''Okay, so I need to analyze this webpage content and provide a score in JSON format. The page is titled "Advanced Robot Arm" and the content says it's a product page for a cleaning robot with AI navigation. Hmm, let me break this down.

First, the title is "Advanced Robot Arm." That sounds a bit generic. I'm not sure if "Robot Arm" refers to a cleaning robot or something else. Maybe it's a robot arm used in manufacturing or something. But the content says it's a cleaning robot with AI navigation. So the title might be a bit misleading because it doesn't specify that it's for cleaning.

Looking at the content, it clearly states it's a cleaning robot with AI navigation. That makes me think the product is specifically designed for cleaning tasks, which is a niche market. Cleaning robots are usually specialized, so that's a positive point. The AI navigation part suggests it can move around autonomously, which is a good feature for cleaning robots because they need to navigate different areas without human intervention.

Now, considering the category. Since it's a cleaning robot, it falls under consumer electronics, specifically home automation or robotics. That makes sense because cleaning robots are often marketed to households as smart home devices.

For the score, I should consider factors like relevance, specificity, and category alignment. The title is somewhat relevant but could be more specific about the function. The content is very specific about it being a cleaning robot with AI, which is good. It's definitely in the right category. So I think a score of 85 makes sense. It's not the highest, but it's solid and aligned with the intended use.

I should also think about any potential issues. The title doesn't clearly state the purpose, which might confuse someone who's not familiar with the product. But the content is clear, so that's not a major issue. The product is specific, which is good for targeting the right audience.

In summary, the product is a cleaning robot with AI navigation, which is a specific and relevant product in the consumer electronics sector. The title could be improved for clarity, but the content is accurate and the category is appropriate. So, a score of 85 seems fair.
</think>

```json
{
  "score": 85,
  "category": "Consumer Electronics",
  "reasoning": "The product is a cleaning robot with AI navigation, specifically targeting the consumer electronics market, particularly home automation. The title is slightly misleading as it doesn't specify the cleaning aspect, but the content accurately describes the product. The category is appropriate, and the product's specificity aids targeting the right audience."
}
```'''

print('Testing JSON extraction...')
extracted = extract_json_from_text(test_text)
print(f'Extracted: {extracted}')
print()

try:
    parsed = json.loads(extracted)
    print('Successfully parsed JSON:')
    print(json.dumps(parsed, indent=2))
except json.JSONDecodeError as e:
    print(f'Failed to parse JSON: {e}')
