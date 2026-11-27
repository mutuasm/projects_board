<template>
  <!-- frappe-ui 1.x editor. RichTextKit keeps everything the old TextEditor
       understood (tables, task lists, images), so saving an existing
       description never drops its markup. -->
  <Editor
    v-model="model"
    :extensions="extensions"
    :placeholder="placeholder"
    :editable="editable"
    :upload-function="uploadFile"
    @blur="(event) => emit('blur', event)"
  >
    <!-- a literal prose-sm here stops EditorContent adding its own prose-v3
         preset on top of the app's .prose-f styles -->
    <EditorContent :class="['prose-sm', editorClass]" />
  </Editor>
</template>

<script setup>
import { upload } from 'frappe-ui'
import { Editor, EditorContent, RichTextKit } from 'frappe-ui/editor'

const model = defineModel({ type: String, default: '' })

defineProps({
  placeholder: { type: String, default: '' },
  editable: { type: Boolean, default: true },
  editorClass: { type: [String, Array, Object], default: '' },
})
const emit = defineEmits(['blur'])

// no @mentions or #tags in this app yet
const extensions = [RichTextKit.configure({ mention: false, tag: false })]

/** Pasted and dropped images upload to Frappe, like the old editor did. */
const uploadFile = (file) => upload(file)
</script>
