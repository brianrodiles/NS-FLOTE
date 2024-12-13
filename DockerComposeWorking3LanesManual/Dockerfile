# Use Ubuntu as the base image
FROM ubuntu:latest

# Install necessary packages: Java and wget for downloading Tomcat
RUN apt-get update && \
    apt-get install -y openjdk-21-jdk wget && \
    apt-get clean

# Check Java installation and unset JAVA_HOME
RUN echo "Java installation directories:" && \
    ls -la /usr/lib/jvm/ && \
    echo "Unsetting JAVA_HOME" && \
    unset JAVA_HOME && \
    java -version

# Download and install Tomcat 9
RUN wget https://downloads.apache.org/tomcat/tomcat-9/v9.0.97/bin/apache-tomcat-9.0.97.tar.gz -O /tmp/tomcat.tar.gz && \
    tar xzvf /tmp/tomcat.tar.gz -C /usr/local && \
    mv /usr/local/apache-tomcat-9.0.97 /usr/local/tomcat && \
    rm /tmp/tomcat.tar.gz

# Copy the ScadaBR.war file to the Tomcat webapps directory
COPY ScadaBR.war /usr/local/tomcat/webapps/

# Expose port 8080 for the application
EXPOSE 8080

# Set the working directory to Tomcat
WORKDIR /usr/local/tomcat

# Start Tomcat when the container launches
CMD ["bin/catalina.sh", "run"]