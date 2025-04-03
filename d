[0;1;32m●[0m nginx.service - A high performance web server and a reverse proxy server
     Loaded: loaded (]8;;file://ubuntu/usr/lib/systemd/system/nginx.service/usr/lib/systemd/system/nginx.service]8;;; [0;1;32menabled[0m; preset: [0;1;32menabled[0m)
     Active: [0;1;32mactive (running)[0m since Fri 2025-02-07 06:32:41 UTC; 1 week 5 days ago
       Docs: ]8;;man:nginx(8)man:nginx(8)]8;;
   Main PID: 251909 (nginx)
      Tasks: 5 (limit: 9431)
     Memory: 8.4M (peak: 13.9M)
        CPU: 7.057s
     CGroup: /system.slice/nginx.service
             ├─[0;38;5;245m251909 "nginx: master process /usr/sbin/nginx -g daemon on; master_process on;"[0m
             ├─[0;38;5;245m679463 "nginx: worker process"[0m
             ├─[0;38;5;245m679464 "nginx: worker process"[0m
             ├─[0;38;5;245m679465 "nginx: worker process"[0m
             └─[0;38;5;245m679466 "nginx: worker process"[0m

Feb 07 06:32:41 ubuntu nginx[251880]: 2025/02/07 06:32:41 [warn] 251880#251880: conflicting server name "216.225.196.110" on 0.0.0.0:80, ignored
Feb 07 06:32:41 ubuntu nginx[251896]: 2025/02/07 06:32:41 [warn] 251896#251896: conflicting server name "216.225.196.110" on 0.0.0.0:80, ignored
Feb 07 06:32:41 ubuntu systemd[1]: Started nginx.service - A high performance web server and a reverse proxy server.
