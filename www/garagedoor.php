<?php

include 'secret.php';

/*

Array
(
    [secret] => ????
    [long] => ???
    [lat] => ???
)

*/


// credit to http://www.geodatasource.com/developers/php
function distance($lat1, $lon1, $lat2, $lon2, $unit) {
	$theta = $lon1 - $lon2;
	$dist = sin(deg2rad($lat1)) * sin(deg2rad($lat2)) +  cos(deg2rad($lat1)) * cos(deg2rad($lat2)) * cos(deg2rad($theta));
	$dist = acos($dist);
	$dist = rad2deg($dist);
	$miles = $dist * 60 * 1.1515;
	$unit = strtoupper($unit);
	
	if ($unit == "K") {
		return ($miles * 1.609344);
	} else if ($unit == "N") {
		return ($miles * 0.8684);
	} else {
		return $miles;
	}
}


if(isset($_POST['secret']) && (trim($_POST['secret']) != '') && (trim($_POST['secret']) == $secret) ) {
    $s=$_POST['secret'];
    echo "Yep.";
    
    if(isset($_POST['lat']) && (trim($_POST['lat']) != '') && isset($_POST['long']) && (trim($_POST['long']) != '') ) {
    	$lat = $_POST['lat'];
    	$long = $_POST['long'];
    	$homeDistance = distance($lat, $long, $home_lat, $home_long, "K");
    	
    	if ($homeDistance > 0.2) {
    		echo "\nYou're more than 200m away.";
    	} else {
    		echo "\nI think you're in the safe zone, less than 200m away.";
			exec($openCommand);
    	}
    	
    } else {
    	echo "\nGot no location";
    }
    
}
else {
    echo "Nope.";
    exit;
}


?>
