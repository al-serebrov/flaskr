$(document).ready(function() {

	$('form input:submit').mouseenter(function() {
		$(this).fadeTo('slow', 1);
	});

	$('form input:submit').mouseleave(function() {
		$(this).fadeTo('slow', 0.5);
	});

});