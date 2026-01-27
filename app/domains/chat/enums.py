from enum import StrEnum


class Intent(StrEnum):
    RECOMMEND_CODY = "RECOMMEND"
    GENERATE_GUIDE = "GENERAL"


class NodeName(StrEnum):
    INTENT_CLASSIFICATION = "intent_classification"
    CODY_INQUIRY_GUIDE = "cody_inquiry_guide"
    RECOMMEND = "recommend"
    TODAYS_PICK = "todays_pick"
