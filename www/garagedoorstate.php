<?php

/*
{
	"doorState": "closed", 
	"carPresent": 1
}

doorState = closed, open, opening, error
carPresent = 1, 0

*/

include 'secret.php';

$state = json_decode(exec($statusCommand));

?><!DOCTYPE html>
<html>
	<head>
		<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
		<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>
		<title>Garage Door State</title>
	</head>
	<body>
		<h1><?php echo $doorFriendlyName; ?> Garage Door</h1>
			<div class='well' style="width: 400px">
			<!--<div class='well'> -->
				Door State <span class="badge" style="background-color:<?php 
				if ($state->{'doorState'} == 'closed') { 
					echo "green"; 
				} elseif ($state->{'doorState'} == 'ventilate') { 
					echo "orange"; 
				} elseif ($state->{'doorState'} == 'opening') { 
					echo "pink"; } 
				else {
					echo "red";
				}
				
				echo "\">". $state->{'doorState'}; 
				?></span><br>
				Car Present <span class="badge" style="background-color:<?php
				if ($state->{'carPresent'} == 1) { 
					echo "green";
				} else { 
					echo "red"; 
				} 
				?>"><span class="glyphicon glyphicon-thumbs-<?php 
				if ($state->{'carPresent'} == 1) { 
					echo "up";
				} else { 
					echo "down"; 
				} 
				?>" aria-hidden="true"></span></span><br>
				Garage temperature <span class="badge"><?php echo $state->{'temperature'}?>&#x2103;</span><i>(Feels like) </i><span class="badge"><?php echo $state->{'heatIndex'}?>&#x2103;</span><br>
				<?php echo $state->{'weatherLocation'}?> temperature <span class="badge"><?php echo $state->{'oTemperature'}?>&#x2103;</span><i>(Feels like) </i><span class="badge"><?php echo $state->{'oHeatIndex'}?>&#x2103;</span><br>
				
				Rainfall last 3 hours: <span class="badge"><?php echo $state->{'rainfall'}?>mm</span><br>
				Humidity<br>
				<ul>
				    <li>Inside: <span class="badge"><?php echo $state->{'humidity'}?>%</span>
				    <li>Outside: <span class="badge"><?php echo $state->{'oHumidity'}?>%</span>
				</ul>
			</div>
	</body>
</html>
