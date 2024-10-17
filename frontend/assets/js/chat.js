var checkout = {};

$(document).ready(function() {
  var $messages = $('.messages-content'),
    d, h, m,
    i = 0;

  const apigClient = apigClientFactory.newClient();

  $(window).load(function() {
    $messages.mCustomScrollbar();
    insertResponseMessage('Hi there!');
  });

  function updateScrollbar() {
    $messages.mCustomScrollbar("update").mCustomScrollbar('scrollTo', 'bottom', {
      scrollInertia: 10,
      timeout: 0
    });
  }

  function setDate() {
    d = new Date()
    if (m != d.getMinutes()) {
      m = d.getMinutes();
      $('<div class="timestamp">' + d.getHours() + ':' + m + '</div>').appendTo($('.message:last'));
    }
  }

  function callChatbotApi(message, sessionAttributes = {}) {

    const body = {
      sessionState: {
        sessionAttributes: sessionAttributes,
        intent: {
          name: 'GreetingIntent',
        },
      },
      inputTranscript: message,
      sessionId: 'user-123',
      bot: {
        botId: '92MRFL2QHD',
        aliasId: 'EP90I7GF1K',
        localeId: 'en_US',
      }
    };

    // Use the API Gateway SDK to make the POST request
    return apigClient.botPost({}, body, {})
      .then(response  => {
        console.log('API response:', response.data);  // Log the response to debug
        return response.data;  // Return the response data
      })
      .catch(error => console.error('Error:', error));
  }
  
  function insertMessage() {
    msg = $('.message-input').val();
    if ($.trim(msg) == '') {
      return false;
    }
    $('<div class="message message-personal">' + msg + '</div>').appendTo($('.mCSB_container')).addClass('new');
    setDate();
    $('.message-input').val(null);
    updateScrollbar();

    callChatbotApi(msg)
    .then((data) => {
      if (!data || !data.response) {  // Check if 'response' exists in the API response
        insertResponseMessage('Oops, something went wrong. Please try again.');
        return;
      }

      console.log('Received response:', data.response);

      // Insert the bot's response message
      insertResponseMessage(data.response);
    })
      .catch((error) => {
        console.log('an error occurred', error);
        insertResponseMessage('Oops, something went wrong. Please try again.');
      });
  }

  $('.message-submit').click(function() {
    insertMessage();
  });

  $(window).on('keydown', function(e) {
    if (e.which == 13) {
      insertMessage();
      return false;
    }
  })

  function insertResponseMessage(content) {
    $('<div class="message loading new"><figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure><span></span></div>').appendTo($('.mCSB_container'));
    updateScrollbar();

    setTimeout(function() {
      $('.message.loading').remove();
      $('<div class="message new"><figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure>' + content + '</div>').appendTo($('.mCSB_container')).addClass('new');
      setDate();
      updateScrollbar();
      i++;
    }, 500);
  }

});
