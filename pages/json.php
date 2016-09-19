<?php
    require_once('config.php');

    $redis = new Redis();
    $redis->connect('localhost', 6379);

    $alives = $redis->hgetall('alives');

    $result = Array();
    foreach($alives as $key => $value) {
        $key = parse_url($key);
        $value = json_decode($value);
        $item = array(
            'host'=> $key['host'],
            'port'=> $key['port'],
            'type'=> $value->type,
            'nm'=> $value->nm,
            'address'=> $value->address
        );
        array_push($result, $item);
    }
    echo json_encode($result);

    $redis->close();
?>
