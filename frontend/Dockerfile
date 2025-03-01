# Build Stage
FROM public.ecr.aws/docker/library/node:22 AS build-step
WORKDIR /build

# Install dependencies
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

# Copy the rest of the source code
COPY . .

# Define build arguments
ARG VITE_DOCS_QA_DELETE_COLLECTIONS
ARG VITE_DOCS_QA_ENABLE_REDIRECT
ARG VITE_DOCS_QA_MAX_UPLOAD_SIZE_MB
ARG VITE_DOCS_QA_STANDALONE_PATH
ARG VITE_GTAG_ID
ARG VITE_QA_FOUNDRY_URL
ARG VITE_USE_LOCAL
ARG VITE_USE_RELATIVE_BASE_URL

# Set environment variables from build arguments
ENV VITE_DOCS_QA_DELETE_COLLECTIONS=${VITE_DOCS_QA_DELETE_COLLECTIONS} \
  VITE_DOCS_QA_ENABLE_REDIRECT=${VITE_DOCS_QA_ENABLE_REDIRECT} \
  VITE_DOCS_QA_MAX_UPLOAD_SIZE_MB=${VITE_DOCS_QA_MAX_UPLOAD_SIZE_MB} \
  VITE_DOCS_QA_STANDALONE_PATH=${VITE_DOCS_QA_STANDALONE_PATH} \
  VITE_GTAG_ID=${VITE_GTAG_ID} \
  VITE_QA_FOUNDRY_URL=${VITE_QA_FOUNDRY_URL} \
  VITE_USE_LOCAL=${VITE_USE_LOCAL} \
  VITE_USE_RELATIVE_BASE_URL=${VITE_USE_RELATIVE_BASE_URL}

# Build the project
RUN yarn build

# Production Stage
FROM public.ecr.aws/docker/library/node:18.2.0 AS production-stage
RUN npm install -g serve
WORKDIR /app
COPY --from=build-step /build/dist /app/dist

EXPOSE 5000
CMD ["serve", "-s", "dist", "-l", "5000"]
