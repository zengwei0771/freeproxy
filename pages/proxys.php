<?php
    require_once('config.php');

    $redis = new Redis();
    $redis->connect('localhost', 6379);

    $alives = $redis->hgetall('alives');

    $redis->close();
?>
<!doctype html>
<html>
    <head>
        <title>国内免费高匿代理服务器IP列表 - <?php echo $site_name;?></title>

        <meta http-equiv="Cache-Control" content="no-transform" />
        <meta http-equiv="Cache-Control" content="no-siteapp" />
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />

        <meta name="keywords" content="<?php echo $site_name;?>,国内免费高匿代理服务器,高匿免费,高匿代理,免费代理,HTTP代理,SOCKS代理,免费代理API" />
        <meta name="description" content="<?php echo $site_name;?>每天提供大量速度稳定的免费高匿代理IP列表,包括http代理、socks代理,每天扫描IP数量10万+,提供免费的查询API;高匿代理ip,免费ip代理,国内ip代理,优质资源只为用户打招,完全免费!" />

        <style>
            body {
                margin: 0;
            }
            a {
                text-decoration: none;
            }
            a:hover {
                color: #0074f2;
                text-decoration: underline;
            }

            .head{
                background-color: #efefef;
                height: 30px;
                font-size: 11px;
                line-height: 30px;
                font-weight: bolder;
                color: #0074a2;
                border-bottom: 1px solid;
            }
            .head > div {
                width: 1024px;
                margin: 0 auto;
            }
            .head * {
                color: #0074a2;
            }

            .body {
                min-height: 640px;
                padding: 40px 0;
            }
            .body > div {
                width: 1024px;
                margin: 20px auto;
            }
            table {
                width: 1024px;
                margin: 20px auto;
                border-collapse: collapse;
            }
            thead {
                background-color: #DDEBEA;
                border-right: 1px solid #DDEBEA;
                color: #484888;
            }
            tbody {
                border-right: 1px dotted #CDDBDA;
            }
            th {
                padding: 6px;
            }
            td {
                text-align: center;
                border-bottom: 1px dotted #CDDBDA;
                border-left: 1px dotted #CDDBDA;
                padding: 4px;
            }

            .body h3 {
                text-align: center;
            }
            .body p {
                text-align: center;
                margin: 0 20px;
                font-size: 13px;
                color: #9DAB8A;
            }

            .bottom {
                font-size: 12px;
                text-align: right;
            }

            .foot {
                border-top: 1px solid;
                color: #aaa;
                text-align: center;
                font-size: 11px;
            }
            .foot a {
                color: #aaa;
                text-decoration: none;
            }
            .foot a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="head">
            <div>
                <div class="left">
                    <a href="http://<?php echo $site_domain;?>/"><?php echo $site_name;?></a>
                </div>
                <div class="right">
                </div>
            </div>
        </div>
        <div class="body">
            <div class="top">
                <h3>免费高匿代理服务器列表</h3>
                <p><?php echo $site_name;?>每天提供大量速度稳定的免费高匿代理IP列表，包括http代理、socks代理，每天扫描IP数量10万+，提供免费的查询API。</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>主机</th>
                        <th>端口</th>
                        <th>匿名度</th>
                        <th>类型</th>
                        <th>所在位置</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach($alives as $key =>$value) {
                        $key = parse_url($key);
                        $value = json_decode($value);
                     ?>
                    <tr>
                        <td><?php echo $key['host'];?></td>
                        <td><?php echo $key['port'];?></td>
                        <td><?php echo $value->nm;?></td>
                        <td><?php echo $value->type;?></td>
                        <td><?php echo $value->address;?></td>
                    </tr>
                    <?php } ?>
                </tbody>
            </table>
            <div class="bottom">
                <a href="/proxys.json" title="国内免费代理高匿服务器IP列表API">免费高匿服务器API</a>
            </div>
        </div>
        <div class="foot">
            <p>&copy;2016
                <a href="http://<?php echo $site_domain;?>/"><?php echo $site_name;?></a>
                <a href="http://www.miitbeian.gov.cn/" target="_blank"><?php echo $beian;?></a>
                <script src="https://s95.cnzz.com/z_stat.php?id=1260222849&web_id=1260222849" language="JavaScript"></script>
            </p>
        </div>
    </body>
</html>
