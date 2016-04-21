<!DOCTYPE HTML>
<head>
<title>KikBrew - MashingControl</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta name="viewport"
    content="width=device-width, initial-scale=1, maximum-scale=1">
<script type="application/x-javascript"> addEventListener("load", function() { setTimeout(hideURLbar, 0); }, false); function hideURLbar(){ window.scrollTo(0,1); } </script>
<link href="css/style.css" rel="stylesheet" type="text/css" media="all" />
<link
    href='http://fonts.googleapis.com/css?family=Open+Sans:400,300,600,700'
    rel='stylesheet' type='text/css'>
<script type="text/javascript" src="js/jquery.js"></script>
<script src="js/jquery.easydropdown.js"></script>
<script src="js/mediaelement-and-player.min.js"></script>
<link rel="stylesheet" href="css/mediaelementplayer.min.css" />
<link rel="stylesheet" href="css/easy-responsive-tabs.css" />
<script src="js/easyResponsiveTabs.js"></script>
<script type="text/javascript">
    $(document).ready(function () {
        $('#horizontalTab').easyResponsiveTabs({
            type: 'default', //Types: default, vertical, accordion           
            width: 'auto', //auto or any width like 600px
            fit: true   // 100% fit in a container
        });
    });
</script>
<script src="js/highcharts.js"></script>
<script src="js/dx.chartjs.js"></script>
</head>

<?php
    if ($_SERVER["REQUEST_METHOD"] == "POST")
    {
        $mode = $_POST['action'];

        if ( $mode == "Start" )
        {
            $temp1 = $_POST['temp1'];
            $time1 = $_POST['time1'];
            $temp2 = $_POST['temp2'];
            $time2 = $_POST['time2'];
            $temp3 = $_POST['temp3'];
            $time3 = $_POST['time3'];
            $temp4 = $_POST['temp4'];
            $time4 = $_POST['time4'];
            $temp5 = $_POST['temp5'];
            $time5 = $_POST['time5'];

            // write "/opt/kikbrew/mashing.profile", remove stop&pause
            $contents = $temp1.",".$time1."\n";
            $contents .= $temp2.",".$time2."\n";
            $contents .= $temp3.",".$time3."\n";
            $contents .= $temp4.",".$time4."\n";
            $contents .= $temp5.",".$time5."\n";
            file_put_contents( "/opt/kikbrew/mashing.profile", $contents );
            
            system( "/bin/rm /opt/kikbrew/stop.mashing" );
            system( "/bin/rm /opt/kikbrew/pause.mashing" );
        }
        if ( $mode == "Stop" )
        {
            // todo: create "/opt/kikbrew/stop.mashing"
            system( "touch /opt/kikbrew/stop.mashing" );
        }
        if ( $mode == "Pauze" )
        {
            // todo: create "/opt/kikbrew/pause.mashing"    
            system( "touch /opt/kikbrew/pause.mashing" );
        }
        if ( $mode == "Resume" )
        {
            // todo: create "/opt/kikbrew/pause.mashing"    
            system( "/bin/rm /opt/kikbrew/pause.mashing" );
        }
    }


    // Definitions
    $modus = array( 0 => "nothing", 1 => "heating", 2 => "holding" );

    // Check the files, get the status
    $state = "unknown";
    if ( file_exists("/opt/kikbrew/stop.mashing") )
    {
        $state = "stopped";
    }
    elseif ( file_exists("/opt/kikbrew/pause.mashing") )
    {
        $state = "pauzed";
    }
    elseif ( file_exists("/opt/kikbrew/mashing.profile") )
    {
        $state = "running";
    }
    else
    {
        $state = "not running, missing profile";
    }

    // Read and process the mashing profile
    // line: temp,time
    $mashprofile = file_get_contents("/opt/kikbrew/mashing.profile");    // read file
    $mashprofilelines = explode( "\n", $mashprofile );

    $mashingprofiletext = "Mashingprofile:<br/>";
    $mashingprofile = array();
    for ( $i=0; $i<count($mashprofilelines); $i++ )
    {
        $elems = explode( ",", $mashprofilelines[ $i ] );
        if ( intval( $elems[1] ) == 0 )
        {
            continue;
        }
        $mashingprofiletext .= $elems[1] . " min at " . $elems[0] . " C<br/>";
        $mashingprofile[ $i ] = array();
        $mashingprofile[ $i ][ "time" ] = intval($elems[1]);
        $mashingprofile[ $i ][ "temp" ] = intval($elems[0]);
    }

    // Read and process the mashing log for xydata and glob vars
    $mashlog = file_get_contents("/opt/kikbrew/mashing.log");    // read file
    $mashloglines = explode( "\n", $mashlog );      // into array line by line
    
    $xdata = "[ ";
    $ydata = "[ ";
    $y2data = "[ ";
    $y3data = "[ ";
    
    $incr = count($mashloglines)/100;
    if ( $incr == 0 )
    {
        $incr=1;
    }

    for ( $i=0; $i<count($mashloglines)-1; $i+=$incr )
    {
        if ( $mashloglines[ $i ][0] == '#' )
        {
            continue;
        }

        $elems = explode( ",", $mashloglines[ $i ] );        
        $xdata .= intval($i/60);
        $ydata .= $elems[2];
        $y2data .= $elems[2];
        $y3data .= $elems[4];
        if ( $i < count($mashloglines)-1 )
        {
            $xdata .= ","; 
            $ydata .= ","; 
            $y2data .= ","; 
            $y3data .= ","; 
        }
    }
    $xdata .= "]"; 
    $ydata .= "]"; 
    $y2data .= "]"; 
    $y3data .= "]"; 

    $elems = explode( ",", $mashloglines[ count( $mashloglines ) - 2 ] );
    $lastupdatetime = $elems[0];
    $acttemp = $elems[2];
    $targetmode = $elems[7];
    $targettemp = $elems[4];
    $targettime = $elems[9];
    $passedtime = $elems[10];
    
    // calculate progresspct
    $mashingprogresspct = 100.0 / (60*$targettime) * $passedtime;
    
    $progresspct = 0;
    $alltime = 0;
    $donetime = 0;
    for ( $i=0; $i<count($mashingprofile); $i++ )
    {
        if ( $targettemp > $mashingprofile[ $i ][ "temp" ] )
        {            
            $donetime += $mashingprofile[ $i ][ "temp" ]*60;
        }
        if ( $targettemp == $mashingprofile[ $i ][ "temp" ] )
        {            
            $donetime += $passedtime;
        }
        $alltime += $mashingprofile[ $i ][ "temp" ]*60;
    }
    $progresspct = 100.0/$alltime*$donetime;

?>

<body>
    <div class="main">
        <div class="wrap">
            <div class="main-top">
                <div class="comment-details">
                    <div class="commnet-user">
                        <img src="images/post-img.png" alt="">
                    </div>
                    <div class="commnet-desc">
                        <p>
                        <h2>
                            Status: <?php echo $state; ?><br /> Updatezeit:
                            <?php echo $lastupdatetime; ?>
                            <br /> Temperatur:
                            <?php echo $acttemp; ?>
                            C /
                            <?php echo $targettemp; ?>
                            C (current)<br /> Modus:
                            <?php echo $modus[ intval( $targetmode ) ]; ?>
                            <br /> Haltezeit :
                            <?php echo $passedtime; ?>
                            sec /
                            <?php echo $targettime*60; ?>
                            sec
                            </p>
                            <div class="progress">
                                <div class="progress-bar"
                                    style="width:<?php echo $mashingprogresspct; ?>%"></div>
                            </div>
                            <?php echo $mashingprofiletext; ?>
                    </div>
                    <div class="clear"></div>
                </div>
                <div class="progress">
                    <div class="progress-bar"
                        style="width:<?php echo $progresspct; ?>%"></div>
                </div>

                <div class="section group">
                    <div class="cont span_2_of_3 main-bottom-left">
                        <div class="charts-elements">
                            <div class="tabs">
                                <!--Horizontal Tab-->
                                <div id="horizontalTab">
                                    <div class="resp-tabs-container">
                                        <div>
                                            <div id="recipes" style="height: 400px; margin: 0 auto"></div>
                                            <script>
                         $(function () {
                            $('#recipes').highcharts({
                            	colors: ['#7cb5ec', '#434348', '#90ed7d', '#f7a35c', '#8085e9', 
                            	         '#f15c80', '#e4d354', '#8085e8', '#8d4653', '#91e8e1'],
                            	         
                                title: {
                                    text: 'Temperatures',
                                    style: {
                                        color: '#222222',
                                        fontWeight: '100'
                                       
                                    }
                                },
                               
                               xAxis: {
                                    categories: <?php echo $xdata; ?>,
                                },
                                
                                yAxis: {
                                    min:0,
                                    max:100,
                                     labels: {
                                        formatter: function() {
                                            return this.value +'C'
                                        }
                                    },
                                     title: {
                                            enabled: false
                                        }
                                },
                                 
                                legend: {
                                    enabled: false
                                },
                                
                                tooltip: {
                                   shared: true,
                                   pointFormat: '{point.y} C, ',
                                    backgroundColor: '#FFFFFF'
                                },
                                
                                legend: {
                                        enabled: true
                                },

                                series: [{            
                                    name: 'Actual',
                                    data:  <?php echo $ydata; ?>,
                                    pointStart: 1
                                },{            
                                    name: 'Projected',
                                    data:  <?php echo $y2data; ?>,
                                    pointStart: 1
                                },{            
                                    name: 'Target',
                                    data:  <?php echo $y3data; ?>,
                                    pointStart: 1
                                }]
                            });
                        });

                         </script>
                                        </div>
                                    <ul class="resp-tabs-list">
                                        <li><span>Temperatures</span></li>
                                        <div class="clear"></div>
                                    </ul>
                                </div>
                            </div>
<hr>
                            <div class="login">
                                <form action="<?php echo htmlspecialchars($_SERVER["PHP_SELF"]);?>" method="post">
                                    <span> Rast 1 <input type="text" name="temp1"
                                        placeholder="temperature" value=<?php echo $mashingprofile[0]["temp"]; ?>> <input type="text"  name="time1"
                                        placeholder="time" value=<?php echo $mashingprofile[0]["time"]; ?>>
                                    </span> <br /> <span> Rast 2 <input type="text"  name="temp2"
                                        placeholder="temperature" value=<?php echo $mashingprofile[1]["temp"]; ?>> <input type="text"  name="time2"
                                        placeholder="time" value=<?php echo $mashingprofile[1]["time"]; ?>>
                                    </span> <br /> <span> Rast 3 <input type="text"  name="temp3"
                                        placeholder="temperature" value=<?php echo $mashingprofile[2]["temp"]; ?>> <input type="text"  name="time3"
                                        placeholder="time" value=<?php echo $mashingprofile[2]["time"]; ?>>
                                    </span> <br /> <span> Rast 4 <input type="text"  name="temp4"
                                        placeholder="temperature" value=<?php echo $mashingprofile[3]["temp"]; ?>> <input type="text"  name="time4"
                                        placeholder="time" value=<?php echo $mashingprofile[3]["time"]; ?>>
                                    </span> <br /> <span> Rast 5 <input type="text"  name="temp5"
                                        placeholder="temperature" value=<?php echo $mashingprofile[4]["temp"]; ?>> <input type="text"  name="time5"
                                        placeholder="time" value=<?php echo $mashingprofile[4]["time"]; ?>>
                                    </span> <br />
                                    <div class="cont span_2_of_3 main-top-right">
                                        <div class="nav">
                                            <ul>
                                                <li><input type="submit" class="my-button"
                                                    name="action" value="Start"></li>
                                                <li><input type="submit" name="action" class="my-button" value="Stop"></li>
                                                <li><input type="submit" name="action" class="my-button"
                                                    value="Pauze"></li>
                                                <li><input type="submit" name="action" class="my-button"
                                                    value="Resume"></li>
                                            </ul>
                                        </div>
                                    </div>
                                    <div class="clear"></div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
                <p />
                <br />
                <div class="copy-right">
                    <p>
                        2014 created by <a href="http://kikmann-online.de" target="_blank">
                            kikmann</a>, css templates from <a href="http://w3layouts.com" target="_blank">w3layouts</a>
                    </p>
                </div>
</body>
</html>
