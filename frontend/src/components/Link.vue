<template>
	<Autocomplete
		ref="autocompleteRef"
		size="sm"
		v-model="value"
		:placeholder="__('Select {0}', [__(doctype)])"
		:options="optionsWithValue"
		:class="disabled ? 'pointer-events-none' : ''"
		:disabled="disabled"
		@update:query="handleQueryUpdate"
	/>
</template>

<script setup>
import { createResource, Autocomplete, debounce } from "frappe-ui"
import { ref, computed, watch } from "vue"

const props = defineProps({
	doctype: {
		type: String,
		required: true,
	},
	modelValue: {
		type: String,
		required: false,
		default: "",
	},
	filters: {
		type: Object,
		default: {},
	},
	disabled: {
		type: Boolean,
		default: false,
	},
})

const emit = defineEmits(["update:modelValue"])

const autocompleteRef = ref(null)
const searchText = ref("")

const value = computed({
	get: () => props.modelValue,
	set: (val) => {
		if (typeof val === "string") {
			emit("update:modelValue", val)
		} else {
			emit("update:modelValue", val?.value || "")
		}
	},
})

const options = createResource({
	url: "frappe.desk.search.search_link",
	params: {
		doctype: props.doctype,
		txt: searchText.value,
		filters: props.filters,
	},
	method: "POST",
	transform: (data) => {
		return data.map((doc) => {
			let title = null
			if (doc.label && doc.label !== doc.value){
				title = doc.label
			} else if (doc.description) {
				title = doc.description.split(",")[0]
			}
			return {
				label: title ? `${title} : ${doc.value}` : doc.value,
				value: doc.value,
			}
		})
	},
})

// Autocomplete only displays a value that is present in `options`. A value set from code
// (e.g. the approver fetched from the Employee) may not be in the first page of search
// results, which made the field look empty. Always keep the current value as an option.
const optionsWithValue = computed(() => {
	const list = options.data || []
	const current = props.modelValue
	if (!current || list.some((o) => o.value === current)) return list
	return [{ label: current, value: current }, ...list]
})

const reloadOptions = (searchTextVal) => {
	options.update({
		params: {
			txt: searchTextVal,
			doctype: props.doctype,
			filters: props.filters,
		},
	})
	options.reload()
}

const handleQueryUpdate = debounce((newQuery) => {
	const val = newQuery || ""
	if (searchText.value === val) return
	searchText.value = val
	reloadOptions(val)
}, 300)

watch(
	() => props.doctype,
	() => {
		if (!props.doctype || props.doctype === options.doctype) return
		reloadOptions("")
	},
	{ immediate: true }
)

watch(
	() => props.filters,
	() => reloadOptions(''),
)
</script>
