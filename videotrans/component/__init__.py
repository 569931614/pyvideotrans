# 直接导入所有 Form 类，避免 PyInstaller 打包时的懒加载问题
from .set_form import (
    BaiduForm, ChatgptForm, DeepLForm, DeepLXForm, TencentForm,
    ElevenlabsForm, InfoForm, AzureForm, GeminiForm, SetLineRole,
    OttForm, CloneForm, SeparateForm, TtsapiForm, GPTSoVITSForm,
    TransapiForm, ArticleForm, AzurettsForm, ChatttsForm, LocalLLMForm,
    ZijiehuoshanForm, HebingsrtForm, DoubaoForm, FishTTSForm, CosyVoiceForm,
    AI302Form, SetINIForm, WatermarkForm, GetaudioForm, HunliuForm,
    VASForm, Fanyisrt, Recognform, Peiyinform, Videoandaudioform,
    Videoandsrtform, OpenAITTSForm, RecognAPIForm, OpenaiRecognAPIForm,
    FormatcoverForm, SubtitlescoverForm,
    SttAPIForm, VolcEngineTTSForm, F5TTSForm, DeepgramForm, ClaudeForm,
    LibreForm, AliForm, ZhipuAIForm, KokoroForm, ParakeetForm,
    ChatterboxForm, SiliconflowForm, DeepseekForm, OpenrouterForm,
    Peiyinformrole, QwenTTSForm, QwenmtForm
)

from .component import (
    DropButton, TextGetdir
)

from .progressbar import ClickableProgressBar
from .set_threads import SetThreadTransDubb
from .set_subtitles_length import SubtitleSettingsDialog

__all__ = [
    # Form classes
    'BaiduForm', 'ChatgptForm', 'DeepLForm', 'DeepLXForm', 'TencentForm',
    'ElevenlabsForm', 'InfoForm', 'AzureForm', 'GeminiForm', 'SetLineRole',
    'OttForm', 'CloneForm', 'SeparateForm', 'TtsapiForm', 'GPTSoVITSForm',
    'TransapiForm', 'ArticleForm', 'AzurettsForm', 'ChatttsForm', 'LocalLLMForm',
    'ZijiehuoshanForm', 'HebingsrtForm', 'DoubaoForm', 'FishTTSForm', 'CosyVoiceForm',
    'AI302Form', 'SetINIForm', 'WatermarkForm', 'GetaudioForm', 'HunliuForm',
    'VASForm', 'Fanyisrt', 'Recognform', 'Peiyinform', 'Videoandaudioform',
    'Videoandsrtform', 'OpenAITTSForm', 'RecognAPIForm', 'OpenaiRecognAPIForm',
    'FormatcoverForm', 'SubtitlescoverForm',
    'SttAPIForm', 'VolcEngineTTSForm', 'F5TTSForm', 'DeepgramForm', 'ClaudeForm',
    'LibreForm', 'AliForm', 'ZhipuAIForm', 'KokoroForm', 'ParakeetForm',
    'ChatterboxForm', 'SiliconflowForm', 'DeepseekForm', 'OpenrouterForm',
    'Peiyinformrole', 'QwenTTSForm', 'QwenmtForm',
    # Component classes
    'DropButton', 'TextGetdir',
    # Other classes
    'ClickableProgressBar', 'SetThreadTransDubb', 'SubtitleSettingsDialog'
]

