build:
	docker compose --env-file compose.env.bak up --build -d

down:
	docker compose --env-file compose.env.bak down

up:
	docker compose --env-file compose.env.bak up -d

deploy:
	python -m deployment.deploy --workspace_fqn ${ws_fqn} --application_set_name ${app_set_name} --ml_repo ${ml_repo} --base_domain_url ${domain} --dockerhub-images-registry ${registry} --secrets-base ${secrets_base}
