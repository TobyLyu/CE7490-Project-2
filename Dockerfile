FROM ubuntu:20.04
# FROM ros:noetic-ros-base

# setup timezone
RUN echo 'Etc/UTC' > /etc/timezone && \
    apt-get update && \
    apt-get install -q -y --no-install-recommends tzdata && \
    rm -rf /var/lib/apt/lists/*

# install packages
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update && apt-get install -q -y --no-install-recommends \
    dirmngr \
    gnupg2 \
    curl \
    ca-certificates \
    sudo \
    git \
    bzip2 \
    libx11-6 \
    tmux \
    wget \
    vim \
    netcat \
    iproute2 \
    iputils-ping \
    iftop \
    iotop \
    screen \
    iperf3 \
    usbutils \
    ntpdate \
    v4l-utils \
    libtinyxml-dev \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# setup environment
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Create a non-root user and switch to it
RUN adduser --disabled-password --gecos '' --shell /bin/bash user 
# \&& chown -R user:user /app
RUN echo "user ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-user
USER user

# All users can use /home/user as their home directory
ENV HOME=/home/user
RUN chmod 777 /home/user

# Install zsh related
RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v1.1.1/zsh-in-docker.sh)" -- \
    -t ys \
    -p git \
    -p https://github.com/zsh-users/zsh-autosuggestions \
    -p https://github.com/zsh-users/zsh-completions \
    -p https://github.com/zsh-users/zsh-history-substring-search \
    -p https://github.com/zsh-users/zsh-syntax-highlighting \
    && sudo echo "set-option -g default-shell /bin/zsh" >> ~/.tmux.conf \
    && sudo chsh -s /bin/zsh


# Copy file
# RUN mkdir -p /home/user/trans_ws/src && \
#     mkdir -p /home/user/rs_ws/src



# COPY ros_ws/src/rs /home/user/rs_ws/src/
# COPY ros_ws/src/trans /home/user/trans_ws/src/


RUN export PYTHONDONTWRITEBYTECODE=abc

WORKDIR /home/user

# # setup entrypoint
COPY entrypoint.sh /
RUN sudo chmod +x /entrypoint.sh

# Set the default command to zsh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/zsh"]