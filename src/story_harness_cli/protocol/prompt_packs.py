from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
from typing import Any, Dict, List

from .io import dump_json_compatible_yaml, load_json_compatible_yaml

PACK_ALIAS_TO_ID = {
    "default": "story-canvas/default",
    "light-novel": "story-canvas/light-novel",
    "web-serial": "story-canvas/web-serial",
}

BUILTIN_PROMPT_PACKS: List[Dict[str, Any]] = [
    {
        "id": "story-canvas/default",
        "version": "1.2",
        "label": "Default Narrative Pack",
        "description": "基础叙事型模板包，覆盖封面、插画、设定图、群像、动作和漫画等第一批通用用途。",
        "supports": {
            "modes": ["text-to-image", "image-to-image", "inpaint"],
            "commercial": True,
        },
        "templates": [
            {
                "id": "character-standard",
                "label": "角色设定图",
                "useCase": "character",
                "complexity": "standard",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n先把{subjectPhrases}立住，再把{detailPhrases}交代清楚。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "character-repaint",
                "label": "角色图重绘",
                "useCase": "character",
                "complexity": "standard",
                "mode": "image-to-image",
                "promptTemplate": "{subject}\n保留既有人设与服装连续性，把{subjectPhrases}和{detailPhrases}再收紧一些。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "scene-standard",
                "label": "章节场景图",
                "useCase": "chapter-scene",
                "complexity": "standard",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n重点抓住{subjectPhrases}，把{detailPhrases}处理得清楚、可信、能直接落图。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "scene-repaint",
                "label": "章节图重绘",
                "useCase": "chapter-scene",
                "complexity": "standard",
                "mode": "image-to-image",
                "promptTemplate": "{subject}\n沿用已有场景锚点，把{subjectPhrases}和{detailPhrases}压得更集中。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "character-sheet-standard",
                "label": "人物设定图",
                "useCase": "character-sheet",
                "complexity": "standard",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n把人物当成长线设定图处理，先稳住{subjectPhrases}，再把{detailPhrases}交代成可反复复用的视觉记忆。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "cover-poster-standard",
                "label": "收藏版海报",
                "useCase": "cover-poster",
                "complexity": "detailed",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n先用{subjectPhrases}立住整张海报的叙事轮廓，再让{detailPhrases}在留白和层次里慢慢长出来。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "commercial-default",
            },
            {
                "id": "ensemble-key-visual-standard",
                "label": "群像主视觉",
                "useCase": "ensemble-key-visual",
                "complexity": "detailed",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n先把{subjectPhrases}理清，再让{detailPhrases}服务群像关系、主次层级和版面呼吸。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "commercial-default",
            },
            {
                "id": "duel-scene-standard",
                "label": "角色对决",
                "useCase": "duel-scene",
                "complexity": "detailed",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n抓住{subjectPhrases}，让{detailPhrases}服务受力、距离和胜负未分的张力。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "chase-escape-standard",
                "label": "追逐逃脱",
                "useCase": "chase-escape",
                "complexity": "detailed",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n先把{subjectPhrases}推出来，再用{detailPhrases}交代速度、危险和空间方向。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "comic-relief-standard",
                "label": "轻松搞笑图",
                "useCase": "comic-relief",
                "complexity": "standard",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n先把{subjectPhrases}打准，再用{detailPhrases}把节奏、夸张点和表情读感做出来。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "promo-standard",
                "label": "宣传图",
                "useCase": "promo",
                "complexity": "detailed",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n先把{subjectPhrases}打出来，再把{detailPhrases}和画面节奏收干净。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "commercial-default",
            },
            {
                "id": "prop-relic-standard",
                "label": "道具遗物图",
                "useCase": "prop-relic",
                "complexity": "standard",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n把{subjectPhrases}当成主角，再把{detailPhrases}交代出材质、年代和象征意味。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "creature-sheet-standard",
                "label": "生物设定图",
                "useCase": "creature-sheet",
                "complexity": "standard",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n先立住{subjectPhrases}，再把{detailPhrases}交代成可信的生物设定。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "manga-panel-standard",
                "label": "漫画单格分镜",
                "useCase": "manga-panel",
                "complexity": "standard",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n按单格分镜处理，先把{subjectPhrases}立住，再让{detailPhrases}服务阅读方向和黑白节奏。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "manga-page-standard",
                "label": "漫画分镜页",
                "useCase": "manga-page",
                "complexity": "detailed",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n按整页漫画分镜处理，先把{subjectPhrases}排清楚，再让{detailPhrases}服务镜头衔接、留白和页内节奏。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
        ],
        "lexicon": {
            "subjectPhrases": {
                "character": ["人物辨识度", "稳定的外貌记忆点", "服装轮廓和配色关系"],
                "character-sheet": ["完整人设立绘", "可长期复用的外轮廓", "服装与体态记忆点"],
                "chapter-scene": ["人物关系和动作焦点", "最有戏的一拍", "可读的空间层次"],
                "cover-poster": ["巨大轮廓主视觉", "一眼识别的世界观符号", "收藏版海报气场"],
                "ensemble-key-visual": ["主角群关系站位", "谁和谁是一伙", "整体势能"],
                "duel-scene": ["对峙双方的力量差", "出手瞬间", "胜负未分的压迫"],
                "chase-escape": ["追逃双方的距离关系", "速度方向", "险些被抓住的一刻"],
                "comic-relief": ["反差感", "表情包级读感", "轻松节奏"],
                "promo": ["单张海报的第一眼冲击", "主卖点", "标题区留白"],
                "prop-relic": ["器物轮廓", "辨识度极强的象征符号", "传说感"],
                "creature-sheet": ["生物体态", "种族辨识度", "威胁或神性"],
                "manga-panel": ["单格焦点", "黑白对比中心", "一眼能懂的动作关系"],
                "manga-page": ["页内主次镜头", "阅读顺序", "整页节奏起伏"],
            },
            "detailPhrases": {
                "character": ["面部特征、发型和服饰材质", "职业气质与姿态习惯"],
                "character-sheet": ["正面信息、配饰、材质和层次", "人物气质与身份痕迹"],
                "chapter-scene": ["光源方向、关键道具与环境质感", "前后景层次和情绪温度"],
                "cover-poster": ["留白、版式和内轮廓叙事层次", "关键建筑、角色关系与象征物"],
                "ensemble-key-visual": ["前后排层次、主副角色分配和标题留白"],
                "duel-scene": ["武器轨迹、受力姿态、空间切割和特效残响"],
                "chase-escape": ["动线、障碍物、环境压迫和镜头前冲感"],
                "comic-relief": ["夸张动作、道具包袱和人物表情"],
                "promo": ["远近层次、主辅视觉节奏和交付整洁度"],
                "prop-relic": ["材质磨损、铭文、能量痕迹和陈列气场"],
                "creature-sheet": ["骨骼结构、皮毛鳞片、器官和生态痕迹"],
                "manga-panel": ["分镜取景、对白留白和明暗块面"],
                "manga-page": ["格与格之间的留白、转场和关键特写"],
            },
            "modePhrases": {
                "text-to-image": ["不要写成分镜指令，直接给出能落图的画面印象。"],
                "image-to-image": ["以输入图的身份和结构为底，只调整镜头、质感和氛围。"],
                "inpaint": ["只修补指定区域，让新内容和原图边缘自然衔接。"],
            },
            "commercialPhrases": {
                "commercial": ["成片保持干净利落，避免影射现成品牌、Logo 和受保护角色元素。"],
            },
        },
        "modifierGroups": [
            {
                "id": "style-cinematic",
                "group": "style",
                "label": "电影感",
                "promptFragment": "电影感构图、分层景深、压住但不闷的戏剧氛围",
                "negativeFragment": "",
                "commercialTags": [],
            },
            {
                "id": "lighting-night",
                "group": "lighting",
                "label": "夜景",
                "promptFragment": "夜景光源、湿润反光和带来叙事感的实景照明",
                "negativeFragment": "",
                "commercialTags": [],
            },
            {
                "id": "composition-portrait",
                "group": "composition",
                "label": "角色近景",
                "promptFragment": "偏角色近景的构图、清楚的面部读感和半身取景",
                "negativeFragment": "",
                "commercialTags": [],
            },
        ],
        "policies": {
            "negativePolicies": [
                {
                    "id": "default-safe",
                    "label": "默认负向",
                    "negativePrompt": "low quality, blurry, distorted hands, duplicate limbs, unreadable face",
                }
            ],
            "commercialPolicies": [
                {
                    "id": "personal-default",
                    "label": "个人默认",
                    "mode": "personal",
                    "extraPrompt": "",
                    "restrictions": [],
                },
                {
                    "id": "commercial-default",
                    "label": "商用默认",
                    "mode": "commercial",
                    "extraPrompt": "成片保持干净利落，避免影射现成品牌、Logo 和受保护角色元素。",
                    "restrictions": ["no-logo-imitation"],
                },
            ],
        },
    },
    {
        "id": "story-canvas/light-novel",
        "version": "1.2",
        "label": "Light Novel Pack",
        "description": "偏轻小说、角色驱动和漫画化表达的模板包。",
        "supports": {
            "modes": ["text-to-image", "image-to-image"],
            "commercial": True,
        },
        "templates": [
            {
                "id": "character-standard",
                "label": "轻小说角色图",
                "useCase": "character",
                "complexity": "standard",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n先把{subjectPhrases}立住，再把{detailPhrases}画得轻盈、清楚、适合长期连载复用。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "scene-standard",
                "label": "轻小说场景图",
                "useCase": "chapter-scene",
                "complexity": "standard",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n重点抓住{subjectPhrases}，把{detailPhrases}处理成轻小说 key visual 那种清亮、好读的状态。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "character-sheet-standard",
                "label": "轻小说设定图",
                "useCase": "character-sheet",
                "complexity": "standard",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n把{subjectPhrases}画得轻盈、清楚、适合长期连载复用，再把{detailPhrases}收得干净可爱。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "cover-poster-standard",
                "label": "轻小说封面海报",
                "useCase": "cover-poster",
                "complexity": "detailed",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n先把{subjectPhrases}立住，再让{detailPhrases}服务轻小说封面那种清亮、梦幻、好读的版面气质。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "comic-relief-standard",
                "label": "轻小说搞笑图",
                "useCase": "comic-relief",
                "complexity": "standard",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n先把{subjectPhrases}打准，再把{detailPhrases}处理成轻小说日常喜剧那种轻巧、夸张、好读的状态。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "manga-panel-standard",
                "label": "轻小说漫画单格",
                "useCase": "manga-panel",
                "complexity": "standard",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n按轻小说漫画单格处理，先把{subjectPhrases}立住，再让{detailPhrases}服务黑白节奏和角色读感。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
            {
                "id": "manga-page-standard",
                "label": "轻小说漫画页",
                "useCase": "manga-page",
                "complexity": "detailed",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n按轻小说漫画页处理，先把{subjectPhrases}排清，再让{detailPhrases}服务页内镜头起伏和阅读顺序。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "personal-default",
            },
        ],
        "lexicon": {
            "subjectPhrases": {
                "character": ["清楚的人物记忆点", "轻快但稳定的人设识别", "表情与姿态的可爱张力"],
                "character-sheet": ["完整立绘", "可爱但稳定的人设轮廓", "适合长期连载复用的服装记忆点"],
                "chapter-scene": ["情绪最亮的一拍", "角色之间的互动焦点", "干净的环境分层"],
                "cover-poster": ["一眼能记住的主角轮廓", "梦幻感", "标题区留白"],
                "comic-relief": ["反差包袱", "表情喜感", "轻快节奏"],
                "manga-panel": ["单格焦点", "黑白对比重心", "角色表情读感"],
                "manga-page": ["页内阅读顺序", "镜头主次", "节奏起伏"],
            },
            "detailPhrases": {
                "character": ["发型、制服或配饰的区分度", "线条轻盈但不单薄的服装层次"],
                "character-sheet": ["配饰、袜靴、发饰和服装层次", "立绘姿态和清楚的体态读感"],
                "chapter-scene": ["清亮光影、前景点缀和角色表情读感"],
                "cover-poster": ["柔和留白、角色关系和光色过渡"],
                "comic-relief": ["夸张动作、小道具和趣味表情"],
                "manga-panel": ["格内明暗块面、镜头取景和对白留白"],
                "manga-page": ["格与格留白、转场和关键特写"],
            },
            "modePhrases": {
                "text-to-image": ["避免堆太多术语，先把角色和情绪的第一印象画准。"],
                "image-to-image": ["保留输入图的人设基础，只微调气氛、配色和镜头表现。"],
            },
        },
        "modifierGroups": [
            {
                "id": "style-anime",
                "group": "style",
                "label": "动漫",
                "promptFragment": "清爽线稿、鲜明表情和偏轻小说的角色表现力",
                "negativeFragment": "",
                "commercialTags": [],
            },
            {
                "id": "lighting-soft",
                "group": "lighting",
                "label": "柔光",
                "promptFragment": "柔和光线、轻亮高光和舒服的肤色层次",
                "negativeFragment": "",
                "commercialTags": [],
            },
        ],
        "policies": {
            "negativePolicies": [
                {
                    "id": "default-safe",
                    "label": "默认负向",
                    "negativePrompt": "blurry, extra fingers, warped anatomy, muddy colors",
                }
            ],
            "commercialPolicies": [
                {
                    "id": "personal-default",
                    "label": "个人默认",
                    "mode": "personal",
                    "extraPrompt": "",
                    "restrictions": [],
                }
            ],
        },
    },
    {
        "id": "story-canvas/web-serial",
        "version": "1.2",
        "label": "Web Serial Pack",
        "description": "偏商业连载、强钩子、强戏剧场面和高识别海报的模板包。",
        "supports": {
            "modes": ["text-to-image", "image-to-image", "inpaint"],
            "commercial": True,
        },
        "templates": [
            {
                "id": "scene-standard",
                "label": "连载高潮场景",
                "useCase": "chapter-scene",
                "complexity": "detailed",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n先把{subjectPhrases}打出来，再把{detailPhrases}往高潮时刻和商业可读性上压。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "commercial-default",
            },
            {
                "id": "promo-standard",
                "label": "连载宣传图",
                "useCase": "promo",
                "complexity": "detailed",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n先把{subjectPhrases}冲出来，再把{detailPhrases}处理成一眼能读懂的宣传图节奏。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "commercial-default",
            },
            {
                "id": "cover-poster-standard",
                "label": "连载封面海报",
                "useCase": "cover-poster",
                "complexity": "detailed",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n先把{subjectPhrases}冲出来，再把{detailPhrases}处理成一眼能记住的商业封面海报节奏。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "commercial-default",
            },
            {
                "id": "ensemble-key-visual-standard",
                "label": "连载群像主视觉",
                "useCase": "ensemble-key-visual",
                "complexity": "detailed",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n先把{subjectPhrases}压住，再让{detailPhrases}服务主角群站位、冲突关系和封面信息密度。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "commercial-default",
            },
            {
                "id": "duel-scene-standard",
                "label": "连载对决图",
                "useCase": "duel-scene",
                "complexity": "detailed",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n抓住{subjectPhrases}，再把{detailPhrases}往高压对决和强阅读性上推。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "commercial-default",
            },
            {
                "id": "chase-escape-standard",
                "label": "连载追逃图",
                "useCase": "chase-escape",
                "complexity": "detailed",
                "mode": "text-to-image",
                "promptTemplate": "{subject}\n先把{subjectPhrases}打出来，再把{detailPhrases}处理成速度感强、方向清楚、险象环生的追逃场面。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
                "defaultNegativePolicyRef": "default-safe",
                "defaultCommercialPolicyRef": "commercial-default",
            },
        ],
        "lexicon": {
            "subjectPhrases": {
                "chapter-scene": ["钩子最强的冲突瞬间", "主角处境反差", "一眼能读懂的动作重心"],
                "cover-poster": ["最能拉点击的巨大主视觉", "世界观钩子", "强识别封面气场"],
                "ensemble-key-visual": ["主角群压迫感", "关系张力", "一眼读懂阵营"],
                "duel-scene": ["力量差", "对杀瞬间", "压迫感最强的一击"],
                "chase-escape": ["追逃距离", "速度方向", "主角命悬一线"],
                "promo": ["最能拉点击的视觉钩子", "高对比主卖点", "适合标题压字的留白"],
            },
            "detailPhrases": {
                "chapter-scene": ["环境压迫感、关键特效和人物受力关系", "前后景层次与危险气味"],
                "cover-poster": ["强对比留白、标题区和世界观象征物"],
                "ensemble-key-visual": ["前后排关系、信息密度和主副角色节奏"],
                "duel-scene": ["武器轨迹、特效爆点和场地切割"],
                "chase-escape": ["动线、障碍物、镜头前冲感和危险余波"],
                "promo": ["主辅元素节奏、爆点信息和商业交付整洁度"],
            },
            "modePhrases": {
                "text-to-image": ["避免平均用力，优先把最抓人的那一下打准。"],
                "image-to-image": ["沿用输入图主体关系，把光影、张力和高潮信息再往前推一步。"],
                "inpaint": ["局部补强时只放大关键冲突，不破坏原有阅读方向。"],
            },
            "commercialPhrases": {
                "commercial": ["交付上保持钩子明确、元素干净，并避开现成 IP 的视觉影射。"],
            },
        },
        "modifierGroups": [
            {
                "id": "lighting-neon-night",
                "group": "lighting",
                "label": "霓虹夜景",
                "promptFragment": "霓虹点色、雨夜反光和高对比夜景照明",
                "negativeFragment": "",
                "commercialTags": [],
            },
            {
                "id": "camera-action",
                "group": "camera",
                "label": "动作镜头",
                "promptFragment": "动态机位、动作冲势和清楚的前后景分离",
                "negativeFragment": "",
                "commercialTags": [],
            },
        ],
        "policies": {
            "negativePolicies": [
                {
                    "id": "default-safe",
                    "label": "默认负向",
                    "negativePrompt": "flat composition, low detail, blurry motion, broken anatomy",
                }
            ],
            "commercialPolicies": [
                {
                    "id": "commercial-default",
                    "label": "商用默认",
                    "mode": "commercial",
                    "extraPrompt": "交付上保持钩子明确、元素干净，并避开现成 IP 的视觉影射。",
                    "restrictions": ["no-logo-imitation"],
                }
            ],
        },
    },
]


def prompt_pack_name_from_ref(pack_ref: Dict[str, Any]) -> str:
    pack_id = str(pack_ref.get("packId") or "").strip()
    if not pack_id:
        return ""
    return pack_id.rsplit("/", 1)[-1]


def default_pack_ref_from_name(name: str, version: str | None = None) -> Dict[str, Any]:
    normalized_name = str(name or "").strip() or "default"
    pack_id = PACK_ALIAS_TO_ID.get(normalized_name, normalized_name)
    return {
        "source": "builtin",
        "packId": pack_id,
        "version": version or _builtin_pack_version(pack_id) or "builtin",
    }


def load_available_prompt_packs(root: Path) -> List[Dict[str, Any]]:
    packs_by_id: dict[str, Dict[str, Any]] = {}
    for pack in BUILTIN_PROMPT_PACKS:
        normalized = _normalize_prompt_pack(pack, source="builtin")
        pack_id = str(normalized.get("id") or "").strip()
        if pack_id:
            packs_by_id[pack_id] = normalized
    for pack in _load_project_prompt_packs(root):
        pack_id = str(pack.get("id") or "").strip()
        if not pack_id:
            continue
        packs_by_id[pack_id] = pack
    return sorted(packs_by_id.values(), key=lambda item: str(item.get("label") or item.get("id") or ""))


def summarize_prompt_pack(pack: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": pack.get("id", ""),
        "name": prompt_pack_name_from_ref({"packId": pack.get("id", "")}),
        "version": pack.get("version", ""),
        "label": pack.get("label", ""),
        "description": pack.get("description", ""),
        "source": pack.get("source", ""),
        "sourceFile": pack.get("sourceFile", ""),
        "supports": pack.get("supports", {}),
        "lexicon": deepcopy(pack.get("lexicon", {})),
        "templates": [
            {
                "id": template.get("id", ""),
                "label": template.get("label", ""),
                "useCase": template.get("useCase", ""),
                "mode": template.get("mode", ""),
                "complexity": template.get("complexity", ""),
                "defaultNegativePolicyRef": template.get("defaultNegativePolicyRef", ""),
                "defaultCommercialPolicyRef": template.get("defaultCommercialPolicyRef", ""),
            }
            for template in pack.get("templates", [])
            if isinstance(template, dict)
        ],
        "modifierGroups": [
            {
                "id": item.get("id", ""),
                "group": item.get("group", ""),
                "label": item.get("label", ""),
                "negativeFragment": item.get("negativeFragment", ""),
            }
            for item in pack.get("modifierGroups", [])
            if isinstance(item, dict)
        ],
        "negativePolicies": [
            {
                "id": item.get("id", ""),
                "label": item.get("label", ""),
                "negativePrompt": item.get("negativePrompt", ""),
            }
            for item in ((pack.get("policies", {}) if isinstance(pack.get("policies"), dict) else {}).get("negativePolicies", []))
            if isinstance(item, dict)
        ],
        "commercialPolicies": [
            {
                "id": item.get("id", ""),
                "label": item.get("label", ""),
                "mode": item.get("mode", ""),
                "restrictions": item.get("restrictions", []),
            }
            for item in ((pack.get("policies", {}) if isinstance(pack.get("policies"), dict) else {}).get("commercialPolicies", []))
            if isinstance(item, dict)
        ],
    }


def serialize_prompt_pack_document(pack: Dict[str, Any], *, include_runtime_meta: bool = True) -> Dict[str, Any]:
    document = {
        "id": pack.get("id", ""),
        "version": pack.get("version", ""),
        "label": pack.get("label", ""),
        "description": pack.get("description", ""),
        "supports": deepcopy(pack.get("supports", {})),
        "lexicon": deepcopy(pack.get("lexicon", {})),
        "templates": [
            {
                "id": template.get("id", ""),
                "label": template.get("label", ""),
                "useCase": template.get("useCase", ""),
                "mode": template.get("mode", ""),
                "complexity": template.get("complexity", ""),
                "promptTemplate": template.get("promptTemplate", ""),
                "defaultNegativePolicyRef": template.get("defaultNegativePolicyRef", ""),
                "defaultCommercialPolicyRef": template.get("defaultCommercialPolicyRef", ""),
            }
            for template in pack.get("templates", [])
            if isinstance(template, dict)
        ],
        "modifierGroups": [
            {
                "id": item.get("id", ""),
                "group": item.get("group", ""),
                "label": item.get("label", ""),
                "promptFragment": item.get("promptFragment", ""),
                "negativeFragment": item.get("negativeFragment", ""),
                "commercialTags": deepcopy(item.get("commercialTags", [])),
            }
            for item in pack.get("modifierGroups", [])
            if isinstance(item, dict)
        ],
        "policies": {
            "negativePolicies": [
                {
                    "id": item.get("id", ""),
                    "label": item.get("label", ""),
                    "negativePrompt": item.get("negativePrompt", ""),
                }
                for item in ((pack.get("policies", {}) if isinstance(pack.get("policies"), dict) else {}).get("negativePolicies", []))
                if isinstance(item, dict)
            ],
            "commercialPolicies": [
                {
                    "id": item.get("id", ""),
                    "label": item.get("label", ""),
                    "mode": item.get("mode", ""),
                    "extraPrompt": item.get("extraPrompt", ""),
                    "restrictions": deepcopy(item.get("restrictions", [])),
                }
                for item in ((pack.get("policies", {}) if isinstance(pack.get("policies"), dict) else {}).get("commercialPolicies", []))
                if isinstance(item, dict)
            ],
        },
    }
    if include_runtime_meta:
        document["name"] = prompt_pack_name_from_ref({"packId": pack.get("id", "")})
        document["source"] = pack.get("source", "")
        document["sourceFile"] = pack.get("sourceFile", "")
        document["writable"] = str(pack.get("source") or "") != "builtin"
    return document


def save_prompt_pack_document(root: Path, raw_pack: Dict[str, Any], *, file_name: str = "") -> Dict[str, Any]:
    packs_dir = root.resolve() / "prompts" / "illustration-packs"
    raw_pack_id = str(raw_pack.get("id") or "").strip()
    if raw_pack_id and _is_builtin_pack_id(raw_pack_id):
        raise ValueError(f"用户模板不能复用系统 pack id: {raw_pack_id}")
    pack_path = _resolve_prompt_pack_save_path(packs_dir, raw_pack, file_name)
    normalized = _normalize_prompt_pack(
        raw_pack,
        source="project",
        source_file=pack_path,
        fallback_pack_id=_derive_project_pack_id(pack_path),
    )
    if not normalized:
        raise ValueError("prompt pack 至少需要可推导的 id、label 或文件名")
    dump_json_compatible_yaml(pack_path, serialize_prompt_pack_document(normalized, include_runtime_meta=False))
    return normalized


def migrate_project_prompt_pack_documents(root: Path, *, dry_run: bool = False) -> Dict[str, Any]:
    packs_dir = root.resolve() / "prompts" / "illustration-packs"
    results: List[Dict[str, Any]] = []
    if not packs_dir.exists():
        return {
            "root": str(root.resolve()),
            "packsDir": str(packs_dir),
            "dryRun": dry_run,
            "packCount": 0,
            "changedCount": 0,
            "writtenCount": 0,
            "results": results,
        }

    for path in sorted(packs_dir.glob("*.yaml")):
        raw = load_json_compatible_yaml(path, {})
        if not isinstance(raw, dict):
            continue
        normalized = _normalize_prompt_pack(
            raw,
            source="project",
            source_file=path,
            fallback_pack_id=_derive_project_pack_id(path),
        )
        serialized = serialize_prompt_pack_document(normalized, include_runtime_meta=False)
        changed = raw != serialized
        if changed and not dry_run:
            dump_json_compatible_yaml(path, serialized)
        results.append(
            {
                "path": str(path),
                "packId": str(normalized.get("id") or ""),
                "label": str(normalized.get("label") or ""),
                "changed": changed,
                "written": changed and not dry_run,
                "templateCount": len(normalized.get("templates", [])),
                "modifierCount": len(normalized.get("modifierGroups", [])),
            }
        )

    return {
        "root": str(root.resolve()),
        "packsDir": str(packs_dir),
        "dryRun": dry_run,
        "packCount": len(results),
        "changedCount": sum(1 for item in results if item["changed"]),
        "writtenCount": sum(1 for item in results if item["written"]),
        "results": results,
    }


def export_prompt_pack_document(
    root: Path,
    illustrations_state: Dict[str, Any],
    *,
    requested_pack_name: str = "",
    file_name: str = "",
) -> Dict[str, Any]:
    resolution = resolve_prompt_pack(root, illustrations_state, requested_pack_name)
    raw_document = serialize_prompt_pack_document(resolution["pack"], include_runtime_meta=False)
    raw_document["id"] = ""
    export_name = str(file_name or resolution.get("packName") or "").strip()
    if not export_name:
        export_name = prompt_pack_name_from_ref({"packId": resolution["packRef"].get("packId", "")}) or "custom-pack"
    return save_prompt_pack_document(root, raw_document, file_name=export_name)


def resolve_prompt_pack(root: Path, illustrations_state: Dict[str, Any], requested_pack_name: str = "") -> Dict[str, Any]:
    available_packs = load_available_prompt_packs(root)
    prompt_system = illustrations_state.get("promptSystem", {})
    pack_ref = prompt_system.get("defaultPack", {}) if isinstance(prompt_system, dict) else {}
    requested_name = str(requested_pack_name or "").strip()
    if requested_name:
        for pack in available_packs:
            candidate_ref = {"packId": pack.get("id", "")}
            if pack.get("id") == requested_name or prompt_pack_name_from_ref(candidate_ref) == requested_name:
                selected_ref = {
                    "source": str(pack.get("source") or "builtin"),
                    "packId": str(pack.get("id", "")),
                    "version": str(pack.get("version", "") or "builtin"),
                }
                return {
                    "pack": pack,
                    "packRef": selected_ref,
                    "packName": prompt_pack_name_from_ref(selected_ref) or requested_name,
                }
        selected_ref = default_pack_ref_from_name(requested_name)
    else:
        selected_ref = {
            "source": str(pack_ref.get("source") or "builtin"),
            "packId": str(pack_ref.get("packId") or default_pack_ref_from_name("default")["packId"]),
            "version": str(pack_ref.get("version") or default_pack_ref_from_name("default")["version"]),
        }

    selected_pack_id = selected_ref["packId"]
    selected_name = prompt_pack_name_from_ref(selected_ref) or "default"
    for pack in available_packs:
        if pack.get("id") == selected_pack_id or prompt_pack_name_from_ref({"packId": pack.get("id", "")}) == selected_name:
            selected_ref["version"] = str(pack.get("version") or selected_ref.get("version") or "")
            return {
                "pack": pack,
                "packRef": selected_ref,
                "packName": selected_name,
            }

    fallback_pack = deepcopy(BUILTIN_PROMPT_PACKS[0])
    fallback_ref = {
        "source": "builtin",
        "packId": fallback_pack["id"],
        "version": fallback_pack["version"],
    }
    return {
        "pack": fallback_pack,
        "packRef": fallback_ref,
        "packName": prompt_pack_name_from_ref(fallback_ref) or "default",
    }


def _load_project_prompt_packs(root: Path) -> List[Dict[str, Any]]:
    packs_dir = root / "prompts" / "illustration-packs"
    if not packs_dir.exists():
        return []
    packs: List[Dict[str, Any]] = []
    for path in sorted(packs_dir.glob("*.yaml")):
        raw = load_json_compatible_yaml(path, {})
        if isinstance(raw, dict):
            normalized = _normalize_prompt_pack(
                raw,
                source="project",
                source_file=path,
                fallback_pack_id=_derive_project_pack_id(path),
            )
            if normalized.get("id"):
                packs.append(normalized)
    return packs


def _builtin_pack_version(pack_id: str) -> str:
    for pack in BUILTIN_PROMPT_PACKS:
        if pack.get("id") == pack_id:
            return str(pack.get("version") or "")
    return ""


def _derive_project_pack_id(path: Path) -> str:
    stem = re.sub(r"[^a-z0-9-]+", "-", path.stem.strip().lower())
    stem = re.sub(r"-{2,}", "-", stem).strip("-")
    if not stem:
        stem = "custom-pack"
    return f"project/{stem}"


def _is_builtin_pack_id(pack_id: str) -> bool:
    normalized = pack_id.strip()
    if not normalized:
        return False
    return normalized in {str(item.get("id") or "").strip() for item in BUILTIN_PROMPT_PACKS}


def _resolve_prompt_pack_save_path(packs_dir: Path, raw_pack: Dict[str, Any], file_name: str) -> Path:
    existing_source_file = Path(str(raw_pack.get("sourceFile") or "")).expanduser() if raw_pack.get("sourceFile") else None
    if existing_source_file is not None:
        existing_path = existing_source_file.resolve()
        if _path_is_within(existing_path, packs_dir.resolve()) and existing_path.suffix.lower() == ".yaml":
            return existing_path
    stem_source = file_name.strip()
    if not stem_source:
        stem_source = str(raw_pack.get("id") or raw_pack.get("name") or raw_pack.get("label") or "").strip()
    stem = _slugify_prompt_pack_file_stem(stem_source)
    return packs_dir / f"{stem}.yaml"


def _slugify_prompt_pack_file_stem(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]+", "-", value.strip().lower().replace("/", "-"))
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized or "custom-pack"


def _path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _normalize_prompt_pack(
    raw_pack: Dict[str, Any],
    *,
    source: str,
    source_file: Path | None = None,
    fallback_pack_id: str = "",
) -> Dict[str, Any]:
    pack_id = str(raw_pack.get("id") or fallback_pack_id).strip()
    if not pack_id:
        return {}
    version = str(raw_pack.get("version") or ("builtin" if source == "builtin" else "project")).strip()
    description = str(raw_pack.get("description") or "").strip()
    templates = _normalize_templates(raw_pack.get("templates"), pack_id)
    modifier_groups = _normalize_modifier_groups(raw_pack.get("modifierGroups"))
    lexicon = _normalize_lexicon(raw_pack.get("lexicon"))
    policies = _normalize_policies(raw_pack.get("policies"))
    supports = _normalize_supports(raw_pack.get("supports"), templates)
    label = str(raw_pack.get("label") or prompt_pack_name_from_ref({"packId": pack_id}) or pack_id).strip()
    normalized = {
        "id": pack_id,
        "version": version or "builtin",
        "label": label,
        "description": description,
        "source": source,
        "supports": supports,
        "lexicon": lexicon,
        "templates": templates,
        "modifierGroups": modifier_groups,
        "policies": policies,
    }
    if source_file is not None:
        normalized["sourceFile"] = str(source_file)
    return normalized


def _normalize_templates(raw_templates: Any, pack_id: str) -> List[Dict[str, Any]]:
    templates: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    for raw in raw_templates if isinstance(raw_templates, list) else []:
        if not isinstance(raw, dict):
            continue
        template_id = str(raw.get("id") or "").strip()
        use_case = str(raw.get("useCase") or "").strip()
        if not template_id or not use_case:
            continue
        if template_id in seen_ids:
            continue
        seen_ids.add(template_id)
        mode = str(raw.get("mode") or "text-to-image").strip() or "text-to-image"
        complexity = str(raw.get("complexity") or "standard").strip() or "standard"
        prompt_template = _normalize_prompt_template(
            str(raw.get("promptTemplate") or "").strip(),
            use_case=use_case,
        )
        templates.append(
            {
                "id": template_id,
                "label": str(raw.get("label") or template_id).strip() or template_id,
                "useCase": use_case,
                "complexity": complexity,
                "mode": mode,
                "promptTemplate": prompt_template,
                "defaultNegativePolicyRef": str(raw.get("defaultNegativePolicyRef") or "").strip(),
                "defaultCommercialPolicyRef": str(raw.get("defaultCommercialPolicyRef") or "").strip(),
                "packId": pack_id,
            }
        )
    return templates


def _normalize_prompt_template(prompt_template: str, *, use_case: str) -> str:
    normalized = str(prompt_template or "").strip()
    if not normalized:
        return _default_prompt_template(use_case)
    if any(
        token in normalized
        for token in (
            "{subjectPhrases}",
            "{detailPhrases}",
            "{modeHint}",
            "{stylePrompt}",
            "{userDirection}",
            "{commercialDirection}",
        )
    ):
        return normalized
    if _is_legacy_prompt_template(normalized):
        return _migrate_legacy_prompt_template(normalized, use_case=use_case)
    return normalized


def _default_prompt_template(use_case: str) -> str:
    templates = {
        "character": "{subject}\n先把{subjectPhrases}立住，再把{detailPhrases}交代清楚。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "character-sheet": "{subject}\n把人物当成长线设定图处理，先稳住{subjectPhrases}，再把{detailPhrases}交代成可反复复用的视觉记忆。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "chapter-scene": "{subject}\n重点抓住{subjectPhrases}，把{detailPhrases}处理得清楚、可信、能直接落图。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "cover-concept": "{subject}\n先用{subjectPhrases}立住整张海报的叙事轮廓，再让{detailPhrases}在留白和层次里慢慢长出来。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "cover-poster": "{subject}\n先用{subjectPhrases}立住整张海报的叙事轮廓，再让{detailPhrases}在留白和层次里慢慢长出来。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "ensemble-key-visual": "{subject}\n先把{subjectPhrases}理清，再让{detailPhrases}服务群像关系、主次层级和版面呼吸。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "duel-scene": "{subject}\n抓住{subjectPhrases}，让{detailPhrases}服务受力、距离和胜负未分的张力。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "chase-escape": "{subject}\n先把{subjectPhrases}推出来，再用{detailPhrases}交代速度、危险和空间方向。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "comic-relief": "{subject}\n先把{subjectPhrases}打准，再用{detailPhrases}把节奏、夸张点和表情读感做出来。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "promo": "{subject}\n先把{subjectPhrases}打出来，再把{detailPhrases}和画面节奏收干净。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "product": "{subject}\n把{subjectPhrases}当成主角，再把{detailPhrases}交代出材质、年代和象征意味。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "prop-relic": "{subject}\n把{subjectPhrases}当成主角，再把{detailPhrases}交代出材质、年代和象征意味。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "creature-sheet": "{subject}\n先立住{subjectPhrases}，再把{detailPhrases}交代成可信的生物设定。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "manga-panel": "{subject}\n按单格分镜处理，先把{subjectPhrases}立住，再让{detailPhrases}服务阅读方向和黑白节奏。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
        "manga-page": "{subject}\n按整页漫画分镜处理，先把{subjectPhrases}排清楚，再让{detailPhrases}服务镜头衔接、留白和页内节奏。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
    }
    return templates.get(
        use_case,
        "{subject}\n先把{subjectPhrases}和{detailPhrases}交代清楚。\n{modeHint}\n{stylePrompt}\n{userDirection}\n{commercialDirection}",
    )


def _is_legacy_prompt_template(prompt_template: str) -> bool:
    legacy_markers = (
        "{styleModifiers}",
        "{userExtraPrompt}",
        "{commercialPrompt}",
        "visual direction:",
        "user direction:",
        "commercial direction:",
    )
    return any(marker in prompt_template for marker in legacy_markers)


def _migrate_legacy_prompt_template(prompt_template: str, *, use_case: str) -> str:
    stripped_lines = [line.strip() for line in prompt_template.splitlines() if line.strip()]
    if not stripped_lines:
        return _default_prompt_template(use_case)
    leading_line = stripped_lines[0] if stripped_lines else "{subject}"
    if "{subject}" not in leading_line:
        leading_line = "{subject}"
    carry_lines: List[str] = []
    for line in stripped_lines[1:]:
        if any(
            marker in line
            for marker in ("{styleModifiers}", "{userExtraPrompt}", "{commercialPrompt}")
        ):
            continue
        normalized = line
        for prefix in ("visual direction:", "user direction:", "commercial direction:"):
            if normalized.lower().startswith(prefix):
                normalized = normalized[len(prefix):].strip()
        if normalized:
            carry_lines.append(normalized)
    migrated_lines = [leading_line]
    migrated_style_line = _build_migrated_style_line(carry_lines)
    if migrated_style_line:
        migrated_lines.append(migrated_style_line)
    migrated_lines.extend(_default_prompt_template(use_case).splitlines()[1:])
    return "\n".join(line for line in migrated_lines if line.strip())


def _build_migrated_style_line(carry_lines: List[str]) -> str:
    if not carry_lines:
        return ""
    joined = "；".join(dict.fromkeys(carry_lines))
    if joined[-1] in "。！？!?.":
        return joined
    return f"画面气质靠近{joined}。"


def _normalize_modifier_groups(raw_modifiers: Any) -> List[Dict[str, Any]]:
    modifiers: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    for raw in raw_modifiers if isinstance(raw_modifiers, list) else []:
        if not isinstance(raw, dict):
            continue
        modifier_id = str(raw.get("id") or "").strip()
        if not modifier_id or modifier_id in seen_ids:
            continue
        seen_ids.add(modifier_id)
        modifiers.append(
            {
                "id": modifier_id,
                "group": str(raw.get("group") or "style").strip() or "style",
                "label": str(raw.get("label") or modifier_id).strip() or modifier_id,
                "promptFragment": str(raw.get("promptFragment") or "").strip(),
                "negativeFragment": str(raw.get("negativeFragment") or "").strip(),
                "commercialTags": [
                    str(item).strip()
                    for item in raw.get("commercialTags", [])
                    if str(item).strip()
                ]
                if isinstance(raw.get("commercialTags"), list)
                else [],
            }
        )
    return modifiers


def _normalize_lexicon(raw_lexicon: Any) -> Dict[str, Dict[str, List[str]]]:
    lexicon = raw_lexicon if isinstance(raw_lexicon, dict) else {}
    normalized = {
        "subjectPhrases": _normalize_phrase_map(lexicon.get("subjectPhrases")),
        "detailPhrases": _normalize_phrase_map(lexicon.get("detailPhrases")),
        "modePhrases": _normalize_phrase_map(lexicon.get("modePhrases")),
        "commercialPhrases": _normalize_phrase_map(lexicon.get("commercialPhrases")),
        "negativePhrases": _normalize_phrase_map(lexicon.get("negativePhrases")),
    }
    return {
        key: value
        for key, value in normalized.items()
        if value
    }


def _normalize_phrase_map(raw_value: Any) -> Dict[str, List[str]]:
    if isinstance(raw_value, (str, list)):
        phrases = _normalize_phrase_list(raw_value)
        return {"common": phrases} if phrases else {}
    if not isinstance(raw_value, dict):
        return {}
    result: Dict[str, List[str]] = {}
    for key, value in raw_value.items():
        normalized_key = str(key or "").strip()
        if not normalized_key:
            continue
        phrases = _normalize_phrase_list(value)
        if phrases:
            result[normalized_key] = phrases
    return result


def _normalize_phrase_list(raw_value: Any) -> List[str]:
    values: List[str] = []
    if isinstance(raw_value, str):
        candidate = raw_value.strip()
        if candidate:
            values.append(candidate)
    elif isinstance(raw_value, list):
        for item in raw_value:
            candidate = str(item or "").strip()
            if candidate and candidate not in values:
                values.append(candidate)
    return values


def _normalize_policies(raw_policies: Any) -> Dict[str, List[Dict[str, Any]]]:
    policies = raw_policies if isinstance(raw_policies, dict) else {}
    negative_policies: List[Dict[str, Any]] = []
    commercial_policies: List[Dict[str, Any]] = []
    seen_negative: set[str] = set()
    seen_commercial: set[str] = set()

    for raw in policies.get("negativePolicies", []) if isinstance(policies.get("negativePolicies"), list) else []:
        if not isinstance(raw, dict):
            continue
        policy_id = str(raw.get("id") or "").strip()
        if not policy_id or policy_id in seen_negative:
            continue
        seen_negative.add(policy_id)
        negative_policies.append(
            {
                "id": policy_id,
                "label": str(raw.get("label") or policy_id).strip() or policy_id,
                "negativePrompt": str(raw.get("negativePrompt") or "").strip(),
            }
        )

    for raw in policies.get("commercialPolicies", []) if isinstance(policies.get("commercialPolicies"), list) else []:
        if not isinstance(raw, dict):
            continue
        policy_id = str(raw.get("id") or "").strip()
        if not policy_id or policy_id in seen_commercial:
            continue
        seen_commercial.add(policy_id)
        commercial_policies.append(
            {
                "id": policy_id,
                "label": str(raw.get("label") or policy_id).strip() or policy_id,
                "mode": str(raw.get("mode") or "personal").strip() or "personal",
                "extraPrompt": str(raw.get("extraPrompt") or "").strip(),
                "restrictions": [
                    str(item).strip()
                    for item in raw.get("restrictions", [])
                    if str(item).strip()
                ]
                if isinstance(raw.get("restrictions"), list)
                else [],
            }
        )

    return {
        "negativePolicies": negative_policies,
        "commercialPolicies": commercial_policies,
    }


def _normalize_supports(raw_supports: Any, templates: List[Dict[str, Any]]) -> Dict[str, Any]:
    supports = raw_supports if isinstance(raw_supports, dict) else {}
    raw_modes = supports.get("modes")
    modes: List[str] = []
    if isinstance(raw_modes, list):
        for item in raw_modes:
            normalized = str(item or "").strip()
            if normalized and normalized not in modes:
                modes.append(normalized)
    if not modes:
        for template in templates:
            mode = str(template.get("mode") or "").strip()
            if mode and mode not in modes:
                modes.append(mode)
    if not modes:
        modes = ["text-to-image"]
    return {
        "modes": modes,
        "commercial": bool(supports.get("commercial", False)),
    }
