<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<FormView
				v-if="formFields.data"
				doctype="Attendance Request"
				v-model="attendanceRequest"
				:isSubmittable="true"
				:fields="formFields.data"
				:id="props.id"
				@validateForm="validateForm"
			/>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { createResource } from "frappe-ui"
import { ref, watch, inject } from "vue"

import FormView from "@/components/FormView.vue"

const employee = inject("$employee")
const __ = inject("$translate")

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

const attendanceRequest = ref({})
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: {
		doctype: "Attendance Request",
	},
	auto: true,

	transform(data) {
		if (props.id) {
			return data
		}

		return data.filter(
			(field) =>
				![
					"employee",
					"employee_name",
					"status",
					"company",
				].includes(field.fieldname)
		)
	},
})

async function setAttendanceRequestApprover(employee_id) {
	if (!employee_id) {
		return
	}

	try {
		const approverResource = createResource({
			url: "frappe.client.get_value",

			params: {
				doctype: "Employee",

				filters: {
					name: employee_id,
				},

				fieldname: "custom_attendance_request_approver",
			},
		})

		await approverResource.fetch()

		const response = approverResource.data

		console.log(
			"Attendance Request Approver response:",
			response
		)

		const approver =
			response?.message?.custom_attendance_request_approver ||
			response?.custom_attendance_request_approver

		if (approver) {
			attendanceRequest.value.custom_attendance_request_approver =
				approver

			console.log(
				"Attendance Request Approver set:",
				approver
			)
		} else {
			attendanceRequest.value.custom_attendance_request_approver = ""

			console.log(
				"No Attendance Request Approver found for Employee:",
				employee_id
			)
		}
	} catch (error) {
		console.error(
			"Failed to get Attendance Request Approver:",
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

		// Only automatically set these values for a new request
		if (!props.id) {
			// Set Employee
			attendanceRequest.value.employee = employee_id

			// Get Attendance Request Approver
			await setAttendanceRequestApprover(employee_id)
		}
	},
	{
		immediate: true,
	}
)

watch(
	() => attendanceRequest.value.employee,

	async (employee_id) => {
		if (!employee_id) {
			return
		}

		// Existing request:
		// if employee is not current employee,
		// make the form read-only
		if (props.id && employee_id !== employee.data.name) {
			setFormReadOnly()
			return
		}

		// New request:
		// fetch approver whenever employee changes
		if (!props.id) {
			await setAttendanceRequestApprover(employee_id)
		}
	}
)

watch(
	() => attendanceRequest.value.from_date,

	(from_date) => {
		if (!attendanceRequest.value.to_date) {
			attendanceRequest.value.to_date = from_date
		}
	}
)
watch(
	() => [
		attendanceRequest.value.from_date,
		attendanceRequest.value.to_date,
	],

	([from_date, to_date]) => {
		validateDates(from_date, to_date)
	}
)
watch(
	() => attendanceRequest.value.half_day,

	(half_day) => {
		if (!formFields.data) {
			return
		}

		const half_day_date = formFields.data.find(
			(field) =>
				field.fieldname === "half_day_date"
		)

		if (half_day_date) {
			half_day_date.hidden = !half_day
		}
	}
)

function setFormReadOnly() {
	if (!formFields.data) {
		return
	}

	formFields.data.map(
		(field) => (field.read_only = true)
	)
}

function validateDates(from_date, to_date) {
	if (!(from_date && to_date)) {
		return
	}

	const error_message =
		from_date > to_date
			? __("To Date cannot be before From Date")
			: ""

	if (!formFields.data) {
		return
	}

	const from_date_field = formFields.data.find(
		(field) =>
			field.fieldname === "from_date"
	)

	if (from_date_field) {
		from_date_field.error_message =
			error_message
	}
}

function validateForm() {
	attendanceRequest.value.employee =
		employee.data.name

	if (
		!attendanceRequest.value
			.custom_attendance_request_approver
	) {
		setAttendanceRequestApprover(
			employee.data.name
		)
	}
}
</script>
