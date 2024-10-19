FROM ubuntu:latest

COPY setup.sh /setup.sh
RUN chmod +x /setup.sh
RUN /setup.sh
RUN rm /setup.sh

COPY startup.sh /startup.sh
RUN chmod +x /startup.sh

CMD ["/startup.sh"]