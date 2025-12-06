const API_BASE_URL = 'https://series-hackathon-service-202642739529.us-east1.run.app';
const API_KEY = process.env.SERIES_API_KEY || '';
const SENDER_NUMBER = process.env.SERIES_SENDER_NUMBER || '+16463029478';

interface SendMessageResponse {
  success?: boolean;
  error?: string;
  [key: string]: unknown;
}

export async function sendMessage(phoneNumber: string, text: string): Promise<SendMessageResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chats`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      chat: { phone_numbers: [phoneNumber] },
      message: { text },
      send_from: SENDER_NUMBER
    })
  });
  return response.json();
}

export async function notifyParticipants(
  participants: string[],
  message: string
): Promise<void> {
  for (const phone of participants) {
    try {
      await sendMessage(phone, message);
    } catch (error) {
      console.error(`Failed to notify ${phone}:`, error);
    }
  }
}
