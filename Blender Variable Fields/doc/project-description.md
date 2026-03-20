# Blender Add-on Design Document: Data Automation & Actions

## 1. Introduction
This Blender Addon facilitates efficient data swapping and task automation within Blender scenes. It enables developers to define customizable fields and actions, allowing non-Blender users to quickly modify predefined datablocks and execute developer-authored tasks without deep Blender knowledge. Primary use case: team-work related Blender workflows and quick Alternative swapping.

## 2. UI Structure
Panel location: "Output" Tab of the Property panel.

### 2.1. Panel Components
1.  **Activate Button:**
    *   Function: Initializes addon, runs setup methods, activates UI Panels.
    *   Action: Spawns "custom_evaluation_template.py" script into internal text datablocks.
2.  **Alternatives List:**
    *   Type: Select List.
    *   Content: `Alternative` datastructures. Each `Alternative` holds a `FieldValue` instance for each `FieldDefinition`.
    *   Actions:
        *   `+` Button: Adds new `Alternative`.
        *   `Alternative` naming supported.
    *   Default: One `Alternative` named "Default" always present. Non-deletable. `FieldValue`s within "Default" are non-editable.
3.  **Field Settings Panel:**
    *   Content: Collection of `FieldDefinition`s exposed by developer.
    *   `Devmode` (True by default):
        *   `+` Button: Adds new `FieldDefinition`.
        *   Editable fields: Name, `default_value`, `type`, `data_path`, `eval_script` path.
        *   `data_path` change triggers validation:
            *   Checks path validity.
            *   Checks type collision (`type(bpy.data.curves["Title"].body)`).
            *   Visual feedback: Exclamation mark icon on collision, hover shows conflict, click auto-sets type.
        *   `Custom Evaluation` checkbox: Exposes `eval_script` (`PointerProperty(type=bpy.types.Text)`) for pre-evaluation script selection.
    *   `Usermode` (`Devmode` False):
        *   Editable fields: Only the `FieldValue.value` of the currently selected non-"Default" `Alternative`.
        *   Non-displayed fields: `type`, `data_path`, `eval_script`.
        *   Non-editable field: `FieldDefinition.name`.
    *   `FieldDefinition.type` options: Standard Blender types (Int, Float, String, Data Block) + Color.
4.  **Action Settings Panel:**
    *   `Devmode`:
        *   `+` Button: Adds new `Action`.
        *   Editable fields: Action Name, `script` (`PointerProperty(type=bpy.types.Text)`) reference.
    *   `Usermode`:
        *   Only displays named buttons for `Action`s.
5.  **General Actions Panel:**
    *   `Update` Button: Reruns evaluation logic for current `Alternative`.
    *   `Auto Update` Toggle: If true, evaluation runs on `FieldValue.value` change.
    *   `Render` Button: Renders scene with current `Alternative` settings.
    *   `Devmode` Toggle: Switches between `Devmode` and `Usermode` UI.
    *   `Deactivate` Button: Deactivates UI, deletes unused addon data (prompts for confirmation).

## 3. Code Structure

### 3.1. Data Structures
*   **`class FieldDefinition(bpy.types.PropertyGroup)`:**
    *   `id: StringProperty(identifier=True)`: Unique, stable identifier for linking `FieldValue`s.
    *   `name: StringProperty()`: Display name for the field.
    *   `type: EnumProperty(...)`: Expected data type (Int, Float, String, Data Block, Color).
    *   `data_path: StringProperty()`: Full Blender data path (e.g., "bpy.data.objects[\"Title\"].location").
    *   `default_value: StringProperty()`: Stores the default/initial value for new `FieldValue`s (used when creating a new `Alternative`).
    *   `eval_script: PointerProperty(type=bpy.types.Text)`: Reference to a custom evaluation script text datablock (CES).
    *   `last_error: StringProperty()`: Stores last error message related to this field.

*   **`class FieldValue(bpy.types.PropertyGroup)`:**
    *   `field_id: StringProperty()`: Links to `FieldDefinition.id`.
    *   `value_int: IntProperty()`: Stores integer value.
    *   `value_float: FloatProperty()`: Stores float value.
    *   `value_string: StringProperty()`: Stores string value.
    *   `value_datablock: PointerProperty(type=bpy.types.ID)`: Stores data block pointer.
    *   `value_color: FloatVectorProperty(size=4, subtype='COLOR')`: Stores color value.
    *   *Note: Use appropriate `value_` property based on `FieldDefinition.type`.*

*   **`class Alternative(bpy.types.PropertyGroup)`:**
    *   `name: StringProperty()`: Name of the alternative.
    *   `field_values: CollectionProperty(type=FieldValue)`: Collection of `FieldValue`s for this alternative.

*   **`class Action(bpy.types.PropertyGroup)`:**
    *   `name: StringProperty()`: Name of the action button.
    *   `script: PointerProperty(type=bpy.types.Text)`: Reference to Python script text datablock to execute.

### 3.2. Data Persistence
*   All user-defined data (`FieldDefinition`s, `Alternative`s, `Action`s) saved with the `.blend` file.

### 3.3. Evaluation Logic (`update` method)
1.  Get `currently_selected_alternative`.
2.  Iterate `FieldDefinition`s:
    *   `field_def = FieldDefinition`
    *   `field_value = currently_selected_alternative.field_values.get(field_def.id)`
    *   Resolve `field_def.data_path` into `owner` and `prop_name`.
    *   `target_blender_data_obj = getattr(owner, prop_name)` (if path valid).
    *   **Custom Evaluation Script (CES) Check (`field_def.eval_script`):**
        *   If `field_def.eval_script` has method `_overwrite_eval(field_value, target_blender_data_obj)`:
            *   Execute `_overwrite_eval`. Exit field processing.
        *   Else If `field_def.eval_script` has method `_pre(field_value, target_blender_data_obj)`:
            *   Execute `_pre`.
        *   **Default Data Setting Logic:**
            *   If `field_def.type` does not match `type(target_blender_data_obj)` and no `_overwrite_eval` in CES:
                *   Attempt standard casting (e.g., int to float, string to int/float).
                *   If casting fails or `data_path` invalid: Set `field_def.last_error`. Continue.
            *   Apply `field_value.value` (after potential casting) to `target_blender_data_obj`.
        *   If `field_def.eval_script` has method `_post(field_value, target_blender_data_obj)`:
            *   Execute `_post`.

### 3.4. Custom Evaluation Script (CES)
*   Template: Addon spawns "custom_evaluation_template.py" on activation (contains example `_pre`, `_post`, `_overwrite_eval` functions).
*   Structure: Blender `Text` datablock containing Python code.
*   Methods:
    *   `_pre(field_value, target_blender_data_obj)`: Runs *before* default data assignment.
    *   `_post(field_value, target_blender_data_obj)`: Runs *after* default data assignment.
    *   `_overwrite_eval(field_value, target_blender_data_obj)`: Runs *instead of* default data assignment logic. Fully responsible for type conversion and data assignment.

### 3.5. Actions
*   Execution: Run `Action.script` immediately when button pressed.
*   Scope: Not part of `update` method evaluation.

## 4. Type Mismatch & Evaluation Behavior

### 4.1. Type Validation
*   If `FieldDefinition.type` != detected `data_path` type, field marked invalid. Warning shown in UI (`Field Settings Panel`).

### 4.2. Evaluation Rules
*   **No CES assigned:**
    *   Field not evaluated.
    *   No data assignment.
    *   `field_def.last_error` stored (e.g., "No CES or type mismatch").
*   **CES assigned (`field_def.eval_script` points to a `Text` datablock):**
    *   Default type validation bypassed.
    *   CES responsible for type conversion and data assignment.
    *   System assumes intentional override by developer.

### 4.3. Execution Order (per field)
1.  If `CES` defines `_overwrite_eval`: Execute `_overwrite_eval`, then exit field processing.
2.  If `FieldDefinition.type` mismatch with `target_blender_data_obj` type:
    *   If `CES` exists: Execute `_pre`, then default data setting (with casting attempt), then `_post`.
    *   Else: Fail, set `field_def.last_error`, exit field processing.
3.  Else (no type mismatch):
    *   If `CES` exists: Execute `_pre`.
    *   Cast `field_value.value` to `field_def.type`.
    *   Apply `field_value.value` via `data_path`.
    *   If `CES` exists: Execute `_post`.

### 4.4. Type Identification for Blender Values
*   Blender values often `bpy_prop_array` (e.g., colors, vectors). `type()` alone is insufficient.
*   **Color Detection Logic:**
    *   If `isinstance(value, (bpy.types.bpy_prop_array, list, tuple))`:
        *   If `len(value) == 3 or len(value) == 4`:
            *   **AND** (`value.bl_rna` or property `subtype` == `'COLOR'`) OR (`value` is a `FloatVector` with `COLOR` subtype):
                *   Classify as `COLOR`.
*   **Principle:** Do NOT rely solely on Python type. Inspect structure (`len`, context, RNA metadata). Arrays can represent vectors, colors, rotations; disambiguate by context.

## 5. Design Principles
*   Default behavior: Strict and type-safe.
*   CES: Explicit override mechanism for developers.
*   No silent failures: All errors recorded (`field_def.last_error`) and visible in UI.
*   Performance: Acknowledge potential for optimization in `update` for large scenes/many fields (future consideration).

## 6. Data Model Behavior
*   **`FieldDefinition`:** Defines field schema (name, type, data_path, CES). Stored once, shared, identified by `id`.
*   **`FieldValue`:** Stores actual value for *each* `Alternative`. Linked to `FieldDefinition` via `field_id`. Holds type-specific `value_` properties.
*   **`Alternative`:** Contains collection of `FieldValue`s. Each `Alternative` = full set of values for all defined fields.
    *   "Default" `Alternative`: Baseline values. Its `FieldValue`s are read-only and derive their initial state from `FieldDefinition.default_value`.