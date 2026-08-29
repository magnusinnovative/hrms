<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<FormView
				v-if="formFields.data"
				doctype="Employee Advance"
				v-model="employeeAdvance"
				:isSubmittable="true"
				:fields="formFields.data"
				:id="props.id"
				:showAttachmentView="true"
				@validateForm="validateForm"
			/>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { createResource } from "frappe-ui"
import { ref, inject, watch } from "vue"

import FormView from "@/components/FormView.vue"
import { useCurrencyConversion } from "@/composables/useCurrencyConversion"

const employee = inject("$employee")

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

// object to store form data
const employeeAdvance = ref({
	employee: employee.data.name,
	employee_name: employee.data.employee_name,
	company: employee.data.company,
	department: employee.data.department,
})

// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Employee Advance" },
	transform(data) {
		const fields = getFilteredFields(data)
		return applyFilters(fields)
	},
})
formFields.reload()

useCurrencyConversion(formFields, employeeAdvance, ["paid_amount"])

// ---- approver / accountant auto-fetch ----
async function setEmployeeAdvanceApprovers(employee_id) {
	if (!employee_id) {
		return
	}

	try {
		const approverResource = createResource({
			url: "frappe.client.get_value",
			params: {
				doctype: "Employee",
				filters: { name: employee_id },
				fieldname: ["custom_advance_approver", "custom_accountant"],
			},
		})

		await approverResource.fetch()

		const response = approverResource.data
		const values = response?.message || response || {}

		console.log("Employee Advance approver/accountant response:", values)

		employeeAdvance.value.custom_advance_approver =
			values.custom_advance_approver || ""

		employeeAdvance.value.custom_accountant =
			values.custom_accountant || ""
	} catch (error) {
		console.error(
			"Failed to get Employee Advance approver/accountant:",
			error
		)
	}
}

watch(
	() => employee?.data?.name,
	async (employee_id) => {
		if (!employee_id) {
			return
		}

		// only auto-set for a new request
		if (!props.id) {
			employeeAdvance.value.employee = employee_id
			await setEmployeeAdvanceApprovers(employee_id)
		}
	},
	{ immediate: true }
)

watch(
	() => employeeAdvance.value.employee,
	async (employee_id) => {
		if (!employee_id) {
			return
		}

		if (!props.id) {
			await setEmployeeAdvanceApprovers(employee_id)
		}
	}
)
// ---- end approver / accountant auto-fetch ----

// helper functions
function getFilteredFields(fields) {
	// reduce noise from the form view by excluding unnecessary fields
	// eg: employee and other details can be fetched from the session user
	const excludeFields = ["naming_series", "base_paid_amount"]
	const extraFields = [
		"employee",
		"employee_name",
		"department",
		"company",
		"more_info_section",
		"pending_amount",
	]
	if (!props.id) excludeFields.push(...extraFields)
	return fields.filter((field) => !excludeFields.includes(field.fieldname))
}

function applyFilters(fields) {
	return fields.map((field) => {
		if (field.fieldname === "advance_account") {
			if (!employeeAdvance.value.currency) return field
			field.linkFilters = {
				root_type: "Asset",
				is_group: 0,
				account_type: "Receivable",
				account_currency: employeeAdvance.value.currency,
				company: employeeAdvance.value.company,
			}
		}
		return field
	})
}

watch(
	() => employeeAdvance.value.currency,
	() => {
		applyFilters(formFields.data)
	}
)

function validateForm() {
	employeeAdvance.value.employee = employee.data.name

	if (!employeeAdvance.value.custom_advance_approver) {
		setEmployeeAdvanceApprovers(employee.data.name)
	}
}
</script>
