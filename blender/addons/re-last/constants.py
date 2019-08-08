import bpy

PGROUP = ""
PREPEAT = "REPEAT"

IC_WHEEL = 'FILE_REFRESH'
IC_KEY_MOVE = 'ARROW_LEFTRIGHT'
IC_KEY_CLICK = 'SORT_ASC'

TYPE_ICONS = dict(
    INT='MESH_CUBE',
    FLOAT='MATSPHERE',
    BOOLEAN='MESH_PLANE',
    ENUM='MESH_GRID',
)

ACTION_ITEMS = (
    ('NONE', "Don't Use", "Don't use", 'X', 0),
    ('EDIT', "Add/Edit Operator",
        "Add/edit the last operator", 'TOOL_SETTINGS', 1),
    ('PIE', "Pie Menu", "Open pie menu", 'MESH_CIRCLE', 2),
    ('RESET', "Reset Properties",
        "Reset properties available for Redo tool "
        "and redo last operator", 'FILE_BLANK', 3),
    ('RESET_ALL', "Reset All Properties",
        "Reset all properties of the last operator and redo it",
        'FILE_BLANK', 4),
    ('F6', "Active Operator Properties",
        "Open Blender's F6 popup for the last operator", 'PROPERTIES', 5),
    ('OVERVIEW', "Overview Hotkeys",
        "Overview Redo tool hotkeys for the last operator",
        'VISIBLE_IPO_ON', 6),
    ('HISTORY', "Repeat History",
        "Open repeat history menu", 'TIME', 7),
    ('SKIP', "Skip Operator",
        "Add active operator to Skip list for Repeat tool",
        'GHOST_DISABLED', 8),
)

KEY_ITEMS = [
    (i.identifier, i.name, "", i.value)
    for k, i in bpy.types.Event.bl_rna.properties["type"].enum_items.items()
]
