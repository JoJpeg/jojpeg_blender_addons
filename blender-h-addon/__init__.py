bl_info = {
	"name": "Hold-to-Hide",
	"author": "Jonas Eschner",
	"version": (1, 0, 0),
	"blender": (5, 1, 0),
	"location": "H key in supported editors",
	"description": "Require holding H to hide, with visual feedback",
	"warning": "",
	"doc_url": "",
	"category": "3D View",
}

import math
import time

import bpy
import gpu
from bpy.props import FloatProperty, FloatVectorProperty, IntProperty
from gpu_extras.batch import batch_for_shader


ADDON_KEYMAPS = []


KEYMAP_SPECS = [
	("Object Mode", "EMPTY", "WINDOW"),
	("Mesh", "EMPTY", "WINDOW"),
	("Curve", "EMPTY", "WINDOW"),
	("Armature", "EMPTY", "WINDOW"),
	("Lattice", "EMPTY", "WINDOW"),
	("Metaball", "EMPTY", "WINDOW"),
	("Pose", "EMPTY", "WINDOW"),
	("Sculpt", "EMPTY", "WINDOW"),
	("Vertex Paint", "EMPTY", "WINDOW"),
	("Weight Paint", "EMPTY", "WINDOW"),
	("Image Paint", "EMPTY", "WINDOW"),
	("Grease Pencil", "EMPTY", "WINDOW"),
	("Grease Pencil Stroke Edit Mode", "EMPTY", "WINDOW"),
	("Sequencer", "SEQUENCE_EDITOR", "WINDOW"),
	("SequencerPreview", "SEQUENCE_EDITOR", "WINDOW"),
	("SequencerCommon", "SEQUENCE_EDITOR", "WINDOW"),
]


def _addon_prefs(context):
	addon = context.preferences.addons.get(__name__)
	if addon:
		return addon.preferences
	return None


def _operator_exists(path):
	current = bpy.ops
	for part in path.split("."):
		current = getattr(current, part, None)
		if current is None:
			return None
	return current


def _poll_and_call(path, **kwargs):
	op = _operator_exists(path)
	if op is None:
		return False
	try:
		if not op.poll():
			return False
	except Exception:
		return False
	try:
		op(**kwargs)
		return True
	except Exception:
		return False


def execute_native_hide(context):
	mode = context.mode
	area = context.area.type if context.area else ""
	obj = context.active_object
	obj_type = obj.type if obj else ""

	if area == "SEQUENCE_EDITOR":
		if _poll_and_call("sequencer.hide", unselected=False):
			return True
		if _poll_and_call("sequencer.mute", unselected=False):
			return True
		return _poll_and_call("sequencer.mute", unselected=True)

	if mode == "OBJECT":
		return _poll_and_call("object.hide_view_set", unselected=False)

	if mode == "EDIT_MESH":
		return _poll_and_call("mesh.hide", unselected=False)
	if mode == "EDIT_CURVE":
		return _poll_and_call("curve.hide", unselected=False)
	if mode == "EDIT_SURFACE":
		return _poll_and_call("curve.hide", unselected=False)
	if mode == "EDIT_ARMATURE":
		return _poll_and_call("armature.hide", unselected=False)
	if mode == "EDIT_LATTICE":
		return _poll_and_call("lattice.hide", unselected=False)
	if mode == "EDIT_METABALL":
		return _poll_and_call("mball.hide_metaelems", unselected=False)
	if mode == "POSE":
		return _poll_and_call("pose.hide", unselected=False)
	if mode == "EDIT_GREASE_PENCIL":
		return _poll_and_call("grease_pencil.hide", unselected=False)

	if obj_type == "MESH":
		if _poll_and_call("mesh.hide", unselected=False):
			return True
	if obj_type in {"CURVE", "SURFACE"}:
		if _poll_and_call("curve.hide", unselected=False):
			return True
	if obj_type == "ARMATURE":
		if _poll_and_call("armature.hide", unselected=False):
			return True
	if obj_type == "LATTICE":
		if _poll_and_call("lattice.hide", unselected=False):
			return True
	if obj_type == "META":
		if _poll_and_call("mball.hide_metaelems", unselected=False):
			return True
	if obj_type == "GREASEPENCIL":
		if _poll_and_call("grease_pencil.hide", unselected=False):
			return True

	return _poll_and_call("object.hide_view_set", unselected=False)


def _draw_circle_2d(shader, center, radius, color, segments=48):
	cx, cy = center
	coords = [(cx, cy)]
	for idx in range(segments + 1):
		angle = (idx / segments) * (2.0 * math.pi)
		coords.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
	batch = batch_for_shader(shader, "TRI_FAN", {"pos": coords})
	shader.uniform_float("color", color)
	batch.draw(shader)


def _draw_progress_ring_2d(shader, center, radius, thickness, color, progress, segments=64):
	if progress <= 0.0:
		return
	cx, cy = center
	sweep = max(1, int(segments * min(progress, 1.0)))
	outer = radius
	inner = max(1.0, radius - thickness)
	coords = []
	for idx in range(sweep + 1):
		angle = (idx / segments) * (2.0 * math.pi) - (math.pi / 2.0)
		ca = math.cos(angle)
		sa = math.sin(angle)
		coords.append((cx + ca * inner, cy + sa * inner))
		coords.append((cx + ca * outer, cy + sa * outer))
	batch = batch_for_shader(shader, "TRI_STRIP", {"pos": coords})
	shader.uniform_float("color", color)
	batch.draw(shader)


class HOLDHIDE_OT_modal_hide(bpy.types.Operator):
	bl_idname = "holdhide.modal_hide"
	bl_label = "Hold to Hide"
	bl_description = "Hold H for a short time to confirm hide"
	bl_options = {"REGISTER", "INTERNAL"}

	_active = False

	def _progress(self, context):
		prefs = _addon_prefs(context)
		duration = prefs.hold_duration if prefs else 0.5
		duration = max(0.05, float(duration))
		elapsed = max(0.0, time.monotonic() - self._start_time)
		return min(1.0, elapsed / duration)

	def _draw_overlay(self, context):
		prefs = _addon_prefs(context)
		if prefs is None:
			return

		shader = gpu.shader.from_builtin("UNIFORM_COLOR")
		dot_color = prefs.indicator_color
		ring_color = (
			min(1.0, dot_color[0] + 0.15),
			min(1.0, dot_color[1] + 0.15),
			min(1.0, dot_color[2] + 0.15),
			dot_color[3],
		)
		base_size = max(2, int(prefs.indicator_size))
		progress = self._progress(context)

		_draw_progress_ring_2d(
			shader,
			self._mouse,
			float(base_size) + 9.0,
			4.0,
			ring_color,
			progress,
		)
		_draw_circle_2d(shader, self._mouse, float(base_size), dot_color)

	def _add_draw_handler(self, context):
		if not context.area:
			return
		space_map = {
			"VIEW_3D": bpy.types.SpaceView3D,
			"IMAGE_EDITOR": bpy.types.SpaceImageEditor,
			"SEQUENCE_EDITOR": bpy.types.SpaceSequenceEditor,
		}
		space_cls = space_map.get(context.area.type)
		if space_cls is None:
			return
		self._draw_space_type = context.area.type
		self._draw_handler = space_cls.draw_handler_add(
			self._draw_overlay,
			(context,),
			"WINDOW",
			"POST_PIXEL",
		)

	def _remove_draw_handler(self):
		if self._draw_handler is None:
			return
		space_map = {
			"VIEW_3D": bpy.types.SpaceView3D,
			"IMAGE_EDITOR": bpy.types.SpaceImageEditor,
			"SEQUENCE_EDITOR": bpy.types.SpaceSequenceEditor,
		}
		space_cls = space_map.get(self._draw_space_type)
		if space_cls is not None:
			try:
				space_cls.draw_handler_remove(self._draw_handler, "WINDOW")
			except Exception:
				pass
		self._draw_handler = None
		self._draw_space_type = ""

	def _tag_redraw(self, context):
		if context.area:
			context.area.tag_redraw()

	def _cleanup(self, context):
		wm = context.window_manager
		if self._timer is not None:
			try:
				wm.event_timer_remove(self._timer)
			except Exception:
				pass
			self._timer = None
		self._remove_draw_handler()
		self._tag_redraw(context)
		type(self)._active = False

	def invoke(self, context, event):
		if type(self)._active:
			return {"CANCELLED"}

		wm = context.window_manager
		self._start_time = 0.0
		self._timer = None
		self._mouse = (0, 0)
		self._draw_handler = None
		self._draw_space_type = ""
		self._triggered = False
		self._start_time = time.monotonic()
		self._mouse = (event.mouse_region_x, event.mouse_region_y)
		self._triggered = False
		self._timer = wm.event_timer_add(0.016, window=context.window)

		self._add_draw_handler(context)
		self._tag_redraw(context)
		wm.modal_handler_add(self)
		type(self)._active = True
		return {"RUNNING_MODAL"}

	def modal(self, context, event):
		if event.type == "MOUSEMOVE":
			self._mouse = (event.mouse_region_x, event.mouse_region_y)
			self._tag_redraw(context)
			return {"RUNNING_MODAL"}

		if event.type == "TIMER":
			self._tag_redraw(context)
			if not self._triggered and self._progress(context) >= 1.0:
				self._triggered = True
				execute_native_hide(context)
				self._cleanup(context)
				return {"FINISHED"}
			return {"RUNNING_MODAL"}

		if event.type == "H" and event.value == "RELEASE":
			self._cleanup(context)
			return {"CANCELLED"}

		if event.type in {"ESC", "RIGHTMOUSE"} and event.value == "PRESS":
			self._cleanup(context)
			return {"CANCELLED"}

		return {"RUNNING_MODAL"}


class HOLDHIDE_Preferences(bpy.types.AddonPreferences):
	bl_idname = __name__

	hold_duration: FloatProperty(
		name="Hold Duration",
		description="Time in seconds H must be held before hide executes",
		default=0.50,
		min=0.05,
		max=3.0,
		subtype="TIME",
	)
	indicator_size: IntProperty(
		name="Indicator Size",
		description="Size of the center indicator at the cursor",
		default=7,
		min=2,
		max=30,
	)
	indicator_color: FloatVectorProperty(
		name="Indicator Color",
		description="Cursor indicator color",
		subtype="COLOR",
		size=4,
		min=0.0,
		max=1.0,
		default=(1.0, 0.15, 0.15, 0.95),
	)

	def draw(self, _context):
		layout = self.layout
		col = layout.column(align=True)
		col.prop(self, "hold_duration")
		col.prop(self, "indicator_size")
		col.prop(self, "indicator_color")


def _register_keymaps():
	wm = bpy.context.window_manager
	keyconfig = wm.keyconfigs.addon if wm else None
	if keyconfig is None:
		return

	for km_name, space_type, region_type in KEYMAP_SPECS:
		km = keyconfig.keymaps.new(name=km_name, space_type=space_type, region_type=region_type)
		try:
			kmi = km.keymap_items.new(HOLDHIDE_OT_modal_hide.bl_idname, "H", "PRESS", head=True)
		except TypeError:
			kmi = km.keymap_items.new(HOLDHIDE_OT_modal_hide.bl_idname, "H", "PRESS")
		ADDON_KEYMAPS.append((km, kmi))


def _unregister_keymaps():
	wm = bpy.context.window_manager if bpy.context else None
	addon_keymaps = wm.keyconfigs.addon.keymaps if wm and wm.keyconfigs and wm.keyconfigs.addon else None

	for km, kmi in reversed(ADDON_KEYMAPS):
		try:
			km.keymap_items.remove(kmi)
		except Exception:
			pass
		try:
			if addon_keymaps is not None and len(km.keymap_items) == 0:
				addon_keymaps.remove(km)
		except Exception:
			pass
	ADDON_KEYMAPS.clear()


classes = (
	HOLDHIDE_OT_modal_hide,
	HOLDHIDE_Preferences,
)


def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	_register_keymaps()


def unregister():
	_unregister_keymaps()
	for cls in reversed(classes):
		try:
			bpy.utils.unregister_class(cls)
		except RuntimeError:
			pass
