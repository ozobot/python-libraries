import typing

type TUserIoPrompt = typing.Literal["string", "number", "boolean", "lineColor", "surfaceColor", "direction"]
type TWebUserIoPrompt = typing.Literal["string", "number", "boolean", "color", "direction"]

# current ari blockly app has inconsistent types for userio prompt - Back instead of Backward and Forward instead of Straight
type TAriUserIoPromptDirections = typing.Literal["Left", "Right", "Back", "Forward"]
