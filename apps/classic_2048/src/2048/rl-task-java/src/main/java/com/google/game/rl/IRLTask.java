package com.google.game.rl;


@SuppressWarnings("unused")
public interface IRLTask {

  void logExtra(Object extra);
  void logScore(Object score);
  void logEpisodeEnd();

  IRLTask EMPTY_TASK = new IRLTask(){

	  @Override
	  public void logExtra(Object extra) {
		  // DO NOTHING
	  }

	  @Override
	  public void logScore(Object score) {
		  // DO NOTHING
	  }

	  @Override
	  public void logEpisodeEnd() {
		  // DO NOTHING
	  }
  };
}
