{{- define "medicore.fullname" -}}
{{ .name }}
{{- end -}}

{{- define "medicore.labels" -}}
app: {{ .name }}
tier: microservice
chart: {{ $.Chart.Name }}-{{ $.Chart.Version }}
{{- end -}}
