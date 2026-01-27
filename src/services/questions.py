"""
Interview Questions Bank

Role-specific questions designed to assess skills, personality, and culture fit.
"""

# Generic opening questions for all applicants
OPENING_QUESTIONS = [
    "Hey there! Thanks for taking the time to chat with me today. Before we dive in, can you tell me a little bit about yourself and what brought you to our community?",
    "What specifically interests you about contributing here, and what do you hope to get out of the experience?",
]

# Role-specific questions
MODERATOR_QUESTIONS = [
    "Tell me about a time you had to handle a conflict between two people. How did you approach it?",
    "If you saw a member being subtly toxic but not technically breaking any rules, how would you handle that?",
    "What's your philosophy on giving warnings versus immediate action?",
    "How do you stay calm when someone is being aggressive or insulting toward you personally?",
    "What hours are you typically most active, and how much time could you realistically dedicate to moderation?",
    "Have you moderated any communities before? What did you learn from that experience?",
    "How would you handle a situation where a popular, well-liked member starts causing problems?",
]

DEVELOPER_QUESTIONS = [
    "What programming languages and technologies are you most comfortable with?",
    "Tell me about a project you're proud of. What challenges did you face and how did you solve them?",
    "How do you approach learning a new technology or framework you've never used before?",
    "Describe your debugging process when something isn't working and you're not sure why.",
    "How do you feel about code reviews? Both giving and receiving feedback?",
    "What's your experience with version control and collaborative development?",
    "How do you balance writing clean, maintainable code versus shipping features quickly?",
    "Tell me about a time you disagreed with a technical decision. How did you handle it?",
]

DESIGNER_QUESTIONS = [
    "What design tools and software are you most experienced with?",
    "Walk me through your design process from concept to final product.",
    "How do you handle feedback or criticism on your work, especially when you disagree?",
    "Tell me about a design you created that you're particularly proud of.",
    "How do you balance creative vision with practical constraints like time or technical limitations?",
    "What inspires your design work? Where do you get your creative ideas?",
    "How do you ensure your designs are accessible and work for different users?",
    "Can you tell me about a time you had to iterate on a design based on user feedback?",
]

CONTENT_CREATOR_QUESTIONS = [
    "What type of content do you enjoy creating the most?",
    "How do you come up with ideas for new content?",
    "Tell me about your experience with content creation. What platforms have you worked with?",
    "How do you handle creative blocks when you're struggling to produce content?",
    "What's your approach to engaging with an audience and building community around your content?",
    "How do you balance quality versus quantity in your content production?",
    "How do you handle negative feedback or criticism on your content?",
]

GENERAL_QUESTIONS = [
    "What do you think makes a Discord community successful and enjoyable to be part of?",
    "How do you typically handle stress or pressure?",
    "Tell me about a time you made a mistake. How did you handle it?",
    "What's something you're currently learning or trying to improve about yourself?",
    "How do you prefer to communicate and collaborate with others?",
]

# Culture fit / personality questions
CULTURE_FIT_QUESTIONS = [
    "Our community values growth and learning from mistakes. Can you share a time when you failed at something and what you learned from it?",
    "We're pretty entrepreneurial here - people take initiative and own their projects. Does that kind of environment appeal to you?",
    "How do you feel about giving and receiving direct, honest feedback?",
    "What does being part of a community mean to you?",
    "Where do you see yourself in this community six months from now?",
]

# Closing questions
CLOSING_QUESTIONS = [
    "Is there anything you'd like to ask me, or anything else you think we should know about you?",
    "Thanks so much for chatting with me today! We'll review everything and get back to you soon. Is there any final thing you'd like to add?",
]

def get_questions_for_role(role: str) -> list[str]:
    """
    Get a complete question set for a specific role.
    
    Args:
        role: The role being applied for (moderator, developer, designer, content, general)
        
    Returns:
        List of questions in interview order
    """
    role = role.lower()
    
    questions = OPENING_QUESTIONS.copy()
    
    if "mod" in role:
        questions.extend(MODERATOR_QUESTIONS[:4])  # Top 4 role questions
    elif "dev" in role or "code" in role or "program" in role:
        questions.extend(DEVELOPER_QUESTIONS[:4])
    elif "design" in role or "art" in role or "graphic" in role:
        questions.extend(DESIGNER_QUESTIONS[:4])
    elif "content" in role or "creat" in role or "video" in role or "stream" in role:
        questions.extend(CONTENT_CREATOR_QUESTIONS[:4])
    else:
        questions.extend(GENERAL_QUESTIONS[:3])
    
    questions.extend(CULTURE_FIT_QUESTIONS[:2])  # Top 2 culture questions
    questions.extend(CLOSING_QUESTIONS)
    
    return questions


# Follow-up prompts based on short/unclear answers
FOLLOW_UP_PROMPTS = [
    "Can you tell me more about that?",
    "That's interesting - could you give me a specific example?",
    "I'd love to hear more details on that.",
    "Could you elaborate a bit?",
]
