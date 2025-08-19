# Use an official Node runtime as a parent image
FROM node:20-alpine

# Set the working directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install --omit=dev

# Copy application source
COPY server.js ./

# Expose the listening port
EXPOSE 3001

# Start the server
CMD ["npm", "start"]